# route_backend_documents.py - DEBUG VERSION

from config import *
from functions_authentication import *
from functions_documents import *
from functions_settings import *
import os
import traceback


def register_route_backend_documents(app):
    @app.route("/api/get_file_content", methods=["POST"])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def get_file_content():
        data = request.get_json()
        user_id = get_current_user_id()
        conversation_id = data.get("conversation_id")
        file_id = data.get("file_id")

        # DEBUG: Log incoming request
        print(
            f"DEBUG get_file_content: user_id={user_id}, conversation_id={conversation_id}, file_id={file_id}"
        )

        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        if not conversation_id or not file_id:
            return jsonify({"error": "Missing conversation_id or id"}), 400

        try:
            _ = cosmos_conversations_container.read_item(
                item=conversation_id, partition_key=conversation_id
            )
        except CosmosResourceNotFoundError:
            return jsonify({"error": "Conversation not found"}), 404
        except Exception as e:
            return jsonify({"error": f"Error reading conversation: {str(e)}"}), 500

        add_file_task_to_file_processing_log(
            document_id=file_id,
            user_id=user_id,
            content="Conversation exists, retrieving file content",
        )
        try:
            query_str = """
                SELECT * FROM c
                WHERE c.conversation_id = @conversation_id
                AND c.id = @file_id
            """
            items = list(
                cosmos_messages_container.query_items(
                    query=query_str,
                    parameters=[
                        {"name": "@conversation_id", "value": conversation_id},
                        {"name": "@file_id", "value": file_id},
                    ],
                    partition_key=conversation_id,
                )
            )

            if not items:
                add_file_task_to_file_processing_log(
                    document_id=file_id,
                    user_id=user_id,
                    content="File not found in conversation",
                )
                return jsonify({"error": "File not found in conversation"}), 404

            add_file_task_to_file_processing_log(
                document_id=file_id,
                user_id=user_id,
                content="File found, processing content: " + str(items),
            )
            items_sorted = sorted(items, key=lambda x: x.get("chunk_index", 0))

            filename = items_sorted[0].get("filename", "Untitled")
            is_table = items_sorted[0].get("is_table", False)

            add_file_task_to_file_processing_log(
                document_id=file_id,
                user_id=user_id,
                content="Combining file content from chunks, filename: "
                + filename
                + ", is_table: "
                + str(is_table),
            )
            combined_parts = []
            for it in items_sorted:
                fc = it.get("file_content", "")

                if isinstance(fc, list):
                    # If file_content is a list of dicts, join their 'content' fields
                    text_chunks = []
                    for chunk in fc:
                        text_chunks.append(chunk.get("content", ""))
                    combined_parts.append("\n".join(text_chunks))
                elif isinstance(fc, str):
                    # If it's already a string, just append
                    combined_parts.append(fc)
                else:
                    # If it's neither a list nor a string, handle as needed (e.g., skip or log)
                    pass

            combined_content = "\n".join(combined_parts)

            if not combined_content:
                add_file_task_to_file_processing_log(
                    document_id=file_id,
                    user_id=user_id,
                    content="Combined file content is empty",
                )
                return jsonify({"error": "File content not found"}), 404

            return (
                jsonify(
                    {
                        "file_content": combined_content,
                        "filename": filename,
                        "is_table": is_table,
                    }
                ),
                200,
            )

        except Exception as e:
            add_file_task_to_file_processing_log(
                document_id=file_id,
                user_id=user_id,
                content="Error retrieving file content: " + str(e),
            )
            return jsonify({"error": f"Error retrieving file content: {str(e)}"}), 500

    @app.route("/api/documents/upload", methods=["POST"])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def api_user_upload_document():
        user_id = get_current_user_id()
        print(f"DEBUG upload: user_id={user_id}")

        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        if "file" not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        files = request.files.getlist("file")
        if not files or all(not f.filename for f in files):
            return jsonify({"error": "No file selected or files have no name"}), 400

        processed_docs = []
        upload_errors = []

        for file in files:
            if not file.filename:
                upload_errors.append(f"Skipped a file with no name.")
                continue

            original_filename = file.filename
            print(f"DEBUG: Processing file: {original_filename}")

            safe_suffix_filename = secure_filename(original_filename)
            file_ext = os.path.splitext(safe_suffix_filename)[1].lower()

            if not allowed_file(original_filename):
                upload_errors.append(f"File type not allowed for: {original_filename}")
                continue

            if not os.path.splitext(original_filename)[1]:
                upload_errors.append(
                    f"Could not determine file extension for: {original_filename}"
                )
                continue

            parent_document_id = str(uuid.uuid4())
            print(
                f"DEBUG: Generated document_id: {parent_document_id} for file: {original_filename}"
            )

            temp_file_path = None
            try:
                sc_temp_files_dir = (
                    "/sc-temp-files" if os.path.exists("/sc-temp-files") else ""
                )
                print(
                    f"DEBUG: Using temp directory: {sc_temp_files_dir if sc_temp_files_dir else 'system temp'}"
                )

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=file_ext, dir=sc_temp_files_dir
                ) as tmp_file:
                    file.save(tmp_file.name)
                    temp_file_path = tmp_file.name
                    print(f"DEBUG: Saved temp file: {temp_file_path}")

            except Exception as e:
                print(f"ERROR saving temp file: {e}")
                print(traceback.format_exc())
                upload_errors.append(
                    f"Failed to save temporary file for {original_filename}: {e}"
                )
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                continue

            try:
                # DEBUG: Log before creating document
                print(
                    f"DEBUG: Creating document in Cosmos DB with document_id={parent_document_id}, user_id={user_id}"
                )

                create_document(
                    file_name=original_filename,
                    user_id=user_id,
                    document_id=parent_document_id,
                    num_file_chunks=0,
                    status="Queued for processing",
                )

                update_document(
                    document_id=parent_document_id,
                    user_id=user_id,
                    percentage_complete=0,
                )

                # DEBUG: Check if background processing config exists
                print(f"DEBUG: Checking background processing configuration...")
                print(
                    f"DEBUG: Document Intelligence endpoint: {os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT', 'NOT SET')}"
                )
                print(
                    f"DEBUG: Document Intelligence key exists: {'Yes' if os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY') else 'No'}"
                )

                # Submit background processing
                future = executor.submit(
                    process_document_upload_background,
                    document_id=parent_document_id,
                    user_id=user_id,
                    temp_file_path=temp_file_path,
                    original_filename=original_filename,
                )

                executor.submit_stored(
                    parent_document_id,
                    process_document_upload_background,
                    document_id=parent_document_id,
                    user_id=user_id,
                    temp_file_path=temp_file_path,
                    original_filename=original_filename,
                )

                processed_docs.append(
                    {"document_id": parent_document_id, "filename": original_filename}
                )
                print(
                    f"DEBUG: Successfully queued document for processing: {parent_document_id}"
                )

            except Exception as e:
                print(f"ERROR queuing document processing: {e}")
                print(traceback.format_exc())
                upload_errors.append(
                    f"Failed to queue processing for {original_filename}: {e}"
                )
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        response_status = 200 if processed_docs and not upload_errors else 207
        if not processed_docs and upload_errors:
            response_status = 400

        return (
            jsonify(
                {
                    "message": f"Processed {len(processed_docs)} file(s). Check status periodically.",
                    "document_ids": [doc["document_id"] for doc in processed_docs],
                    "processed_filenames": [doc["filename"] for doc in processed_docs],
                    "errors": upload_errors,
                }
            ),
            response_status,
        )

    @app.route("/api/documents", methods=["GET"])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def api_get_user_documents():
        user_id = get_current_user_id()
        print(f"DEBUG get_documents: user_id={user_id}")

        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        page = request.args.get("page", default=1, type=int)
        page_size = request.args.get("page_size", default=10, type=int)
        search_term = request.args.get("search", default=None, type=str)
        classification_filter = request.args.get(
            "classification", default=None, type=str
        )
        author_filter = request.args.get("author", default=None, type=str)
        keywords_filter = request.args.get("keywords", default=None, type=str)
        abstract_filter = request.args.get("abstract", default=None, type=str)

        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10

        query_conditions = ["c.user_id = @user_id"]
        query_params = [{"name": "@user_id", "value": user_id}]
        param_count = 0

        if search_term:
            param_name = f"@search_term_{param_count}"
            query_conditions.append(
                f"(CONTAINS(LOWER(c.file_name ?? ''), LOWER({param_name})) OR CONTAINS(LOWER(c.title ?? ''), LOWER({param_name})))"
            )
            query_params.append({"name": param_name, "value": search_term})
            param_count += 1

        if classification_filter:
            param_name = f"@classification_{param_count}"
            if classification_filter.lower() == "none":
                query_conditions.append(
                    f"(NOT IS_DEFINED(c.document_classification) OR c.document_classification = null OR c.document_classification = '')"
                )
            else:
                query_conditions.append(f"c.document_classification = {param_name}")
                query_params.append(
                    {"name": param_name, "value": classification_filter}
                )
                param_count += 1

        if author_filter:
            param_name = f"@author_{param_count}"
            query_conditions.append(
                f"EXISTS(SELECT VALUE a FROM a IN c.authors WHERE CONTAINS(LOWER(a), LOWER({param_name})))"
            )
            query_params.append({"name": param_name, "value": author_filter})
            param_count += 1

        if keywords_filter:
            param_name = f"@keywords_{param_count}"
            query_conditions.append(
                f"EXISTS(SELECT VALUE k FROM k IN c.keywords WHERE CONTAINS(LOWER(k), LOWER({param_name})))"
            )
            query_params.append({"name": param_name, "value": keywords_filter})
            param_count += 1

        if abstract_filter:
            param_name = f"@abstract_{param_count}"
            query_conditions.append(
                f"CONTAINS(LOWER(c.abstract ?? ''), LOWER({param_name}))"
            )
            query_params.append({"name": param_name, "value": abstract_filter})
            param_count += 1

        where_clause = " AND ".join(query_conditions)

        try:
            count_query_str = f"SELECT VALUE COUNT(1) FROM c WHERE {where_clause}"
            print(f"DEBUG Count Query: {count_query_str}")
            print(f"DEBUG Count Params: {query_params}")

            count_items = list(
                cosmos_user_documents_container.query_items(
                    query=count_query_str,
                    parameters=query_params,
                    enable_cross_partition_query=True,
                )
            )
            total_count = count_items[0] if count_items else 0
            print(f"DEBUG: Total documents found: {total_count}")

        except Exception as e:
            print(f"ERROR executing count query: {e}")
            print(traceback.format_exc())
            return jsonify({"error": f"Error counting documents: {str(e)}"}), 500

        try:
            offset = (page - 1) * page_size
            data_query_str = f"""
                SELECT *
                FROM c
                WHERE {where_clause}
                ORDER BY c._ts DESC
                OFFSET {offset} LIMIT {page_size}
            """
            print(f"DEBUG Data Query: {data_query_str}")

            docs = list(
                cosmos_user_documents_container.query_items(
                    query=data_query_str,
                    parameters=query_params,
                    enable_cross_partition_query=True,
                )
            )

            # DEBUG: Log document IDs returned
            print(f"DEBUG: Retrieved {len(docs)} documents")
            for doc in docs:
                print(
                    f"  - Document: id={doc.get('id')}, file_name={doc.get('file_name')}, status={doc.get('status')}"
                )

        except Exception as e:
            print(f"ERROR executing data query: {e}")
            print(traceback.format_exc())
            return jsonify({"error": f"Error fetching documents: {str(e)}"}), 500

        try:
            legacy_q = """
                SELECT VALUE COUNT(1)
                FROM c
                WHERE c.user_id = @user_id
                    AND NOT IS_DEFINED(c.percentage_complete)
            """
            legacy_docs = list(
                cosmos_user_documents_container.query_items(
                    query=legacy_q,
                    parameters=[{"name": "@user_id", "value": user_id}],
                    enable_cross_partition_query=True,
                )
            )
            legacy_count = legacy_docs[0] if legacy_docs else 0
        except Exception as e:
            print(f"ERROR executing legacy query: {e}")
            legacy_count = 0

        return (
            jsonify(
                {
                    "documents": docs,
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "needs_legacy_update_check": legacy_count > 0,
                }
            ),
            200,
        )

    @app.route("/api/documents/<document_id>", methods=["GET"])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def api_get_user_document(document_id):
        user_id = get_current_user_id()
        print(f"DEBUG get_document: user_id={user_id}, document_id={document_id}")

        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        return get_document(user_id, document_id)

    @app.route("/api/documents/<document_id>", methods=["PATCH"])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def api_patch_user_document(document_id):
        user_id = get_current_user_id()
        print(f"DEBUG patch_document: user_id={user_id}, document_id={document_id}")

        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        data = request.get_json()
        print(f"DEBUG: Patch data received: {data}")

        if "title" in data:
            update_document(
                document_id=document_id, user_id=user_id, title=data["title"]
            )
        if "abstract" in data:
            update_document(
                document_id=document_id, user_id=user_id, abstract=data["abstract"]
            )
        if "keywords" in data:
            if isinstance(data["keywords"], list):
                update_document(
                    document_id=document_id, user_id=user_id, keywords=data["keywords"]
                )
            else:
                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    keywords=[kw.strip() for kw in data["keywords"].split(",")],
                )
        if "publication_date" in data:
            update_document(
                document_id=document_id,
                user_id=user_id,
                publication_date=data["publication_date"],
            )
        if "document_classification" in data:
            update_document(
                document_id=document_id,
                user_id=user_id,
                document_classification=data["document_classification"],
            )
        if "authors" in data:
            if isinstance(data["authors"], list):
                update_document(
                    document_id=document_id, user_id=user_id, authors=data["authors"]
                )
            else:
                update_document(
                    document_id=document_id, user_id=user_id, authors=[data["authors"]]
                )

        try:
            return jsonify({"message": "Document metadata updated successfully"}), 200
        except Exception as e:
            print(f"ERROR updating document: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/documents/<document_id>", methods=["DELETE"])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def api_delete_user_document(document_id):
        user_id = get_current_user_id()
        print(f"DEBUG delete_document: user_id={user_id}, document_id={document_id}")

        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        try:
            # DEBUG: Check if document exists before deletion
            print(f"DEBUG: Checking if document exists in Cosmos DB...")
            try:
                existing_doc = cosmos_user_documents_container.read_item(
                    item=document_id, partition_key=user_id
                )
                print(
                    f"DEBUG: Found document to delete: {existing_doc.get('file_name')}"
                )
            except Exception as e:
                print(f"DEBUG: Document not found in Cosmos DB: {e}")
                return jsonify({"error": "Document not found"}), 404

            # Delete the document
            print(f"DEBUG: Deleting document from Cosmos DB...")
            delete_document(user_id, document_id)

            # Delete associated chunks
            print(f"DEBUG: Deleting document chunks...")
            delete_document_chunks(document_id)

            print(f"DEBUG: Document {document_id} deleted successfully")
            return jsonify({"message": "Document deleted successfully"}), 200

        except Exception as e:
            print(f"ERROR deleting document: {e}")
            print(traceback.format_exc())
            return jsonify({"error": f"Error deleting document: {str(e)}"}), 500

    @app.route("/api/documents/<document_id>/extract_metadata", methods=["POST"])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def api_extract_user_metadata(document_id):
        user_id = get_current_user_id()
        print(f"DEBUG extract_metadata: user_id={user_id}, document_id={document_id}")

        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        settings = get_settings()
        if not settings.get("enable_extract_meta_data"):
            return jsonify({"error": "Metadata extraction not enabled"}), 403

        # Queue the background task
        future = executor.submit(
            process_metadata_extraction_background,
            document_id=document_id,
            user_id=user_id,
        )

        executor.submit_stored(
            f"{document_id}_metadata",
            process_metadata_extraction_background,
            document_id=document_id,
            user_id=user_id,
        )

        return (
            jsonify(
                {
                    "message": "Metadata extraction has been queued. Check document status periodically.",
                    "document_id": document_id,
                }
            ),
            200,
        )

    @app.route("/api/get_citation", methods=["POST"])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def get_citation():
        data = request.get_json()
        user_id = get_current_user_id()
        citation_id = data.get("citation_id")

        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        if not citation_id:
            return jsonify({"error": "Missing citation_id"}), 400

        try:
            search_client_user = CLIENTS["search_client_user"]
            chunk = search_client_user.get_document(key=citation_id)
            if chunk.get("user_id") != user_id:
                return jsonify({"error": "Unauthorized access to citation"}), 403

            return (
                jsonify(
                    {
                        "cited_text": chunk.get("chunk_text", ""),
                        "file_name": chunk.get("file_name", ""),
                        "page_number": chunk.get("chunk_sequence", 0),
                    }
                ),
                200,
            )

        except ResourceNotFoundError:
            pass

        try:
            search_client_group = CLIENTS["search_client_group"]
            group_chunk = search_client_group.get_document(key=citation_id)

            return (
                jsonify(
                    {
                        "cited_text": group_chunk.get("chunk_text", ""),
                        "file_name": group_chunk.get("file_name", ""),
                        "page_number": group_chunk.get("chunk_sequence", 0),
                    }
                ),
                200,
            )

        except ResourceNotFoundError:
            return jsonify({"error": "Citation not found in user or group docs"}), 404

        except Exception as e:
            return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    @app.route("/api/get_document_citations", methods=["POST"])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def get_document_citations():
        """
        Returns all citations for a document with enhanced metadata
        for the PDF viewer with highlighting capabilities
        """
        data = request.get_json()
        user_id = get_current_user_id()
        document_id = data.get("document_id")
        file_name = data.get("file_name", "")

        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        if not document_id:
            return jsonify({"error": "Missing document_id"}), 400

        try:
            # Search for all citations belonging to this document
            search_client_user = CLIENTS["search_client_user"]

            # Query to find all chunks for this document
            if file_name:
                # Search by file name
                search_query = f'file_name:"{file_name}"'
                filter_query = f"user_id eq '{user_id}'"
            else:
                # Search by document ID
                search_query = f'document_id:"{document_id}"'
                filter_query = f"user_id eq '{user_id}'"

            search_results = search_client_user.search(
                search_text=search_query,
                filter=filter_query,
                select=[
                    "id",
                    "chunk_text",
                    "file_name",
                    "chunk_sequence",
                    "document_id",
                    "user_id",
                ],
                top=1000,  # Get all chunks for the document
            )

            citations = []
            for result in search_results:
                # Verify user ownership
                if result.get("user_id") != user_id:
                    continue

                citation = {
                    "citationId": result.get("id"),
                    "pageNumber": result.get("chunk_sequence", 1),
                    "textContent": result.get("chunk_text", ""),
                    "documentId": result.get("document_id"),
                    "fileName": result.get("file_name", ""),
                    # Placeholder for bounding boxes - will be enhanced in Phase 3
                    "boundingBoxes": [],
                }
                citations.append(citation)

            # Try group documents if no user documents found
            if not citations:
                try:
                    search_client_group = CLIENTS["search_client_group"]

                    # Use the same search query but without user filter for group documents
                    group_search_results = search_client_group.search(
                        search_text=search_query,
                        select=[
                            "id",
                            "chunk_text",
                            "file_name",
                            "chunk_sequence",
                            "document_id",
                        ],
                        top=1000,
                    )

                    for result in group_search_results:
                        citation = {
                            "citationId": result.get("id"),
                            "pageNumber": result.get("chunk_sequence", 1),
                            "textContent": result.get("chunk_text", ""),
                            "documentId": result.get("document_id"),
                            "fileName": result.get("file_name", ""),
                            "boundingBoxes": [],
                        }
                        citations.append(citation)

                except Exception as group_error:
                    print(f"Group search error: {str(group_error)}")

            # Sort citations by page number
            citations.sort(key=lambda x: x["pageNumber"])

            return (
                jsonify(
                    {
                        "documentId": document_id,
                        "fileName": file_name
                        or (citations[0]["fileName"] if citations else ""),
                        "citations": citations,
                        "totalCitations": len(citations),
                    }
                ),
                200,
            )

        except Exception as e:
            print(f"Error in get_document_citations: {str(e)}")
            return (
                jsonify({"error": f"Error retrieving document citations: {str(e)}"}),
                500,
            )

    @app.route("/api/documents/upgrade_legacy", methods=["POST"])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def api_upgrade_legacy_user_documents():
        user_id = get_current_user_id()
        count = upgrade_legacy_documents(user_id)
        return (
            jsonify({"message": f"Upgraded {count} document(s) to the new format."}),
            200,
        )
