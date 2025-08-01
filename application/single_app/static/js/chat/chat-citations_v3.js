// chat-citations.js

import { showToast } from "./chat-toast.js";
import { showLoadingIndicator, hideLoadingIndicator } from "./chat-loading-indicator.js";
import { toBoolean } from "./chat-utils.js";
import { fetchFileContent } from "./chat-input-actions.js";
// --- NEW IMPORT ---
import { getDocumentMetadata } from './chat-documents.js';
// ------------------

const chatboxEl = document.getElementById("chatbox");

export function parseDocIdAndPage(citationId) {
  // ... (keep existing implementation)
  const underscoreIndex = citationId.lastIndexOf("_");
  if (underscoreIndex === -1) {
    return { docId: null, pageNumber: null };
  }
  const docId = citationId.substring(0, underscoreIndex);
  const pageNumber = citationId.substring(underscoreIndex + 1);
  return { docId, pageNumber };
}

export function parseCitations(message) {
  // ... (keep existing implementation)
  const citationRegex = /\(Source:\s*([^,]+),\s*Page(?:s)?:\s*([^)]+)\)\s*((?:\[#.*?\]\s*)+)/gi;

  return message.replace(citationRegex, (whole, filename, pages, bracketSection) => {
    let filenameHtml;
    if (/^https?:\/\/.+/i.test(filename.trim())) {
      filenameHtml = `<a href="${filename.trim()}" target="_blank" rel="noopener noreferrer">${filename.trim()}</a>`;
    } else {
      filenameHtml = filename.trim();
    }

    const bracketMatches = bracketSection.match(/\[#.*?\]/g) || [];
    const pageToRefMap = {};

    bracketMatches.forEach((match) => {
      let inner = match.slice(2, -1).trim();
      const refs = inner.split(/[;,]/);
      refs.forEach((r) => {
        let ref = r.trim();
        if (ref.startsWith('#')) ref = ref.slice(1);
        const parts = ref.split('_');
        const pageNumber = parts.pop();
        // Ensure docId part is also captured if needed, though ref is the full ID here
        // const docIdPart = parts.join('_');
        pageToRefMap[pageNumber] = ref; // ref is the full citationId like 'docid_pagenum'
      });
    });

    function getDocPrefix(ref) {
      const underscoreIndex = ref.lastIndexOf('_');
      return underscoreIndex === -1 ? ref : ref.slice(0, underscoreIndex + 1);
    }

    const pagesTokens = pages.split(/,/).map(tok => tok.trim());
    const linkedTokens = pagesTokens.map(token => {
      const dashParts = token.split(/[–—-]/).map(p => p.trim());

      if (dashParts.length === 2 && dashParts[0] && dashParts[1]) {
        const startNum = parseInt(dashParts[0], 10);
        const endNum   = parseInt(dashParts[1], 10);

        if (!isNaN(startNum) && !isNaN(endNum)) {
          let discoveredPrefix = '';
          if (pageToRefMap[startNum]) {
            discoveredPrefix = getDocPrefix(pageToRefMap[startNum]);
          } else if (pageToRefMap[endNum]) {
            discoveredPrefix = getDocPrefix(pageToRefMap[endNum]);
          }

          const increment = startNum <= endNum ? 1 : -1;
          const pageAnchors = [];
          for (let p = startNum; increment > 0 ? p <= endNum : p >= endNum; p += increment) {
            if (!pageToRefMap[p] && discoveredPrefix) {
              pageToRefMap[p] = discoveredPrefix + p;
            }
            // Use the full citation ID (ref) from the map for the anchor
            pageAnchors.push(buildAnchorIfExists(String(p), pageToRefMap[p]));
          }
          return pageAnchors.join(', ');
        }
      }

      const singleNum = parseInt(token, 10);
      if (!isNaN(singleNum)) {
        const ref = pageToRefMap[singleNum];
        return buildAnchorIfExists(token, ref);
      }
      return token;
    });

    const linkedPagesText = linkedTokens.join(', ');
    return `(Source: ${filenameHtml}, Pages: ${linkedPagesText})`;
  });
}


export function buildAnchorIfExists(pageStr, citationId) {
  // ... (keep existing implementation)
   if (!citationId) {
    return pageStr;
  }
  // Ensure citationId doesn't have a leading # if passed accidentally
  const cleanCitationId = citationId.startsWith('#') ? citationId.slice(1) : citationId;
  return `<a href="#" class="citation-link" data-citation-id="${cleanCitationId}" target="_blank" rel="noopener noreferrer">${pageStr}</a>`;
}

// --- MODIFIED: fetchCitedText handles errors more gracefully ---
export function fetchCitedText(citationId) {
  showLoadingIndicator();
  fetch("/api/get_citation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ citation_id: citationId }),
  })
    .then((response) => {
        if (!response.ok) {
            // Try to parse error message from JSON response if possible
            return response.json().then(errData => {
                // Throw an error that includes the server's message
                throw new Error(errData.error || `Server responded with status ${response.status}`);
            }).catch(() => {
                 // If parsing JSON fails, throw a generic error
                 throw new Error(`Server responded with status ${response.status}`);
            });
        }
        return response.json();
    })
    .then((data) => {
      hideLoadingIndicator();

      // Check for expected data fields explicitly
      if (data.cited_text !== undefined && data.file_name && data.page_number !== undefined) {
        showCitedTextPopup(data.cited_text, data.file_name, data.page_number);
      } else if (data.error) { // Handle explicit errors from server even on 200 OK
         showToast(`Could not retrieve citation: ${data.error}`, "warning");
      } else {
         // Handle cases where the response is OK but data is missing
         console.warn("Received citation response but required data is missing:", data);
         showToast("Citation data incomplete.", "warning");
      }
    })
    .catch((error) => {
      hideLoadingIndicator();
      console.error("Error fetching cited text:", error);
      // Show the error message from the caught error
      showToast(`Error fetching citation: ${error.message}`, "danger");
    });
}

export function showCitedTextPopup(citedText, fileName, pageNumber) {
  // ... (keep existing implementation)
  let modalContainer = document.getElementById("citation-modal");
  if (!modalContainer) {
    modalContainer = document.createElement("div");
    modalContainer.id = "citation-modal";
    modalContainer.classList.add("modal", "fade");
    modalContainer.tabIndex = -1;
    modalContainer.setAttribute("aria-hidden", "true");

    modalContainer.innerHTML = `
      <div class="modal-dialog modal-dialog-scrollable modal-xl modal-fullscreen-sm-down">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Source: ${fileName}, Page: ${pageNumber}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <pre id="cited-text-content"></pre>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modalContainer);
  } else {
    const modalTitle = modalContainer.querySelector(".modal-title");
    if (modalTitle) {
      modalTitle.textContent = `Source: ${fileName}, Page: ${pageNumber}`;
    }
  }

  const citedTextContent = document.getElementById("cited-text-content");
  if (citedTextContent) {
    citedTextContent.textContent = citedText;
  }

  const modal = new bootstrap.Modal(modalContainer);
  modal.show();
}

export function showImagePopup(imageSrc) {
  // ... (keep existing implementation)
  let modalContainer = document.getElementById("image-modal");
  if (!modalContainer) {
    modalContainer = document.createElement("div");
    modalContainer.id = "image-modal";
    modalContainer.classList.add("modal", "fade");
    modalContainer.tabIndex = -1;
    modalContainer.setAttribute("aria-hidden", "true");

    modalContainer.innerHTML = `
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-body text-center">
            <img
              id="image-modal-img"
              src=""
              alt="Generated Image"
              class="img-fluid"
            />
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modalContainer);
  }
  const modalImage = modalContainer.querySelector("#image-modal-img");
  if (modalImage) {
    modalImage.src = imageSrc;
  }
  const modal = new bootstrap.Modal(modalContainer);
  modal.show();
}

// --- MODIFIED: Added citationId parameter and fallback in catch ---
export function showPdfModal(docId, pageNumber, citationId) {
  const fetchUrl = `/view_pdf?doc_id=${encodeURIComponent(docId)}&page=${encodeURIComponent(pageNumber)}`;

  let pdfModal = document.getElementById("pdf-modal");
  if (!pdfModal) {
    pdfModal = document.createElement("div");
    pdfModal.id = "pdf-modal";
    pdfModal.classList.add("modal", "fade");
    pdfModal.tabIndex = -1;
    pdfModal.innerHTML = `
      <div class="modal-dialog modal-dialog-scrollable modal-xl modal-fullscreen-sm-down">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Citation +/- one page</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body" style="height:80vh;">
            <iframe
              id="pdf-iframe"
              src=""
              style="width:100%; height:100%; border:none;"
            ></iframe>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(pdfModal);
  }

  showLoadingIndicator();

  fetch(fetchUrl)
    .then(async (resp) => {
      // Keep existing success logic
      if (!resp.ok) {
         // Throw an error to be caught by the .catch block
         const errorText = await resp.text(); // Try to get more info
         throw new Error(`Failed to load PDF. Status: ${resp.status}. ${errorText.substring(0, 100)}`);
      }
       hideLoadingIndicator(); // Hide indicator ONLY on successful fetch response start

      const newPage = resp.headers.get("X-Sub-PDF-Page") || "1";
      const blob = await resp.blob();
      const pdfBlobUrl = URL.createObjectURL(blob);
      const iframeSrc = pdfBlobUrl + `#page=${newPage}`;
      const iframe = pdfModal.querySelector("#pdf-iframe");
      if (iframe) {
        iframe.src = iframeSrc;
        // Ensure modal is shown AFTER iframe src is set
         const modalInstance = new bootstrap.Modal(pdfModal);
         modalInstance.show();
      } else {
          // Should not happen if modal structure is correct
          console.error("PDF iframe element not found after creating modal.");
          showToast("Error displaying PDF viewer.", "danger");
           // Fallback if iframe fails to load? Maybe too complex.
           // fetchCitedText(citationId);
      }

    })
    .catch((error) => {
      // --- FALLBACK LOGIC ---
      hideLoadingIndicator(); // Ensure indicator is hidden on error
      console.error("Error fetching PDF, falling back to text citation:", error);
      // showToast(`Could not load PDF preview: ${error.message}. Falling back to text citation.`, "warning");
      // Call the text-based citation fetcher
      fetchCitedText(citationId);
      // --- END FALLBACK ---

      // Ensure modal doesn't linger if PDF fetch failed before showing
      const maybeModalInstance = bootstrap.Modal.getInstance(pdfModal);
      if (maybeModalInstance) {
          maybeModalInstance.hide();
      }
    });
}
// --------------------------------------------------------------------

// --- MODIFIED: Event Listener Logic ---
if (chatboxEl) {
  chatboxEl.addEventListener("click", (event) => {
    const target = event.target.closest('a'); // Find the nearest ancestor anchor tag

    // Check if it's an inline citation link OR a hybrid citation button
    if (target && (target.matches("a.citation-link") || target.matches("a.citation-button.hybrid-citation-link"))) {
      event.preventDefault();
      const citationId = target.getAttribute("data-citation-id");
      if (!citationId) {
          console.warn("Citation link/button clicked but data-citation-id is missing.");
          showToast("Cannot process citation: Missing ID.", "warning");
          return;
      }

      const { docId, pageNumber } = parseDocIdAndPage(citationId);

      // Safety check: Ensure docId and pageNumber were parsed correctly
      if (!docId || !pageNumber) {
          console.warn(`Could not parse docId/pageNumber from citationId: ${citationId}. Falling back to text citation.`);
          // showToast("Could not identify document source, showing text.", "info");
          fetchCitedText(citationId); // Fallback to text if parsing fails
          return;
      }

      // --- Logic to decide between PDF and Text ---
      const useEnhancedGlobally = toBoolean(window.enableEnhancedCitations);
      let attemptEnhanced = false; // Default to not attempting enhanced

      if (useEnhancedGlobally) {
          // console.log(`Checking metadata for docId: ${docId}`);
          const docMetadata = getDocumentMetadata(docId); // Fetch metadata

          // Decide based on metadata:
          // Attempt enhanced if:
          // 1. Metadata found AND enhanced_citations is NOT explicitly false
          // 2. Metadata not found (assume enhanced might be possible, rely on error fallback)
          if (!docMetadata) {
              // console.log(`Metadata not found for ${docId}, attempting enhanced citation (will fallback on error).`);
              attemptEnhanced = true;
          } else if (docMetadata.enhanced_citations === false) {
              // console.log(`Metadata found for ${docId}, enhanced_citations is false. Using text citation.`);
              attemptEnhanced = false; // Explicitly disabled for this doc
          } else {
              // console.log(`Metadata found for ${docId}, enhanced_citations is true or undefined. Attempting enhanced citation.`);
              attemptEnhanced = true; // Includes cases where metadata exists but enhanced_citations is true, null, or undefined
          }
      } else {
        // console.log("Global enhanced citations disabled. Using text citation.");
        attemptEnhanced = false; // Globally disabled
      }

      // --- Execute based on the decision ---
      if (attemptEnhanced) {
          // console.log(`Attempting Enhanced PDF Modal for ${docId}, citationId ${citationId}`);
          // Use the new enhanced PDF viewer with progressive fallback
          showCitationWithFallback(citationId, docId);
      } else {
          // console.log(`Fetching Text Citation for ${citationId}`);
          // Use text citation if globally disabled OR explicitly disabled for this doc OR if parsing failed earlier
          fetchCitedText(citationId);
      }
      // --- End Logic ---

    } else if (target && target.matches("a.file-link")) { // Keep existing file link logic
      event.preventDefault();
      const fileId = target.getAttribute("data-file-id");
      const conversationId = target.getAttribute("data-conversation-id");
      if (fileId && conversationId) { // Add checks
        fetchFileContent(conversationId, fileId);
      } else {
        console.warn("File link clicked but missing data-file-id or data-conversation-id");
        showToast("Could not open file: Missing information.", "warning");
      }
    } else if (event.target && event.target.classList.contains("generated-image")) { // Keep existing image logic
        // Use event.target directly here as it's the image itself
      const imageSrc = event.target.getAttribute("data-image-src");
      if (imageSrc) {
          showImagePopup(imageSrc);
      }
    }
    // Clicks on web citation buttons (a.citation-button.web-citation-link) are handled
    // natively by the browser because they have a valid href and target="_blank".
    // No specific JS handling needed here unless you want to add tracking etc.
  });
}

// ======================================
// ENHANCED PDF CITATION VIEWER - Phase 2
// ======================================

/**
 * Enhanced PDF Citation Viewer Class
 * Provides full PDF viewing with citation highlighting and navigation
 */
class EnhancedPDFCitationViewer {
  constructor(modalId) {
    this.modalId = modalId;
    this.currentDocument = null;
    this.pdfDoc = null;
    this.citations = [];
    this.currentCitationIndex = 0;
    this.currentPage = 1;
    this.zoomLevel = 1.0;
    this.canvas = null;
    this.context = null;
    this.highlightOverlay = null;
    this.modal = null;
  }

  async loadDocument(docId, citationData) {
    console.log('DEBUG: EnhancedPDFCitationViewer.loadDocument called', { docId, citationData });
    
    try {
      this.currentDocument = docId;
      this.citations = citationData.citations || [];
      console.log('DEBUG: Citations loaded:', this.citations.length);
      
      // Load PDF document using PDF.js
      const pdfUrl = `/view_document/${encodeURIComponent(docId)}`;
      console.log('DEBUG: PDF URL:', pdfUrl);
      
      console.log('DEBUG: Calling pdfjsLib.getDocument');
      const loadingTask = pdfjsLib.getDocument(pdfUrl);
      console.log('DEBUG: Loading task created, awaiting promise');
      
      this.pdfDoc = await loadingTask.promise;
      console.log('DEBUG: PDF document loaded successfully, pages:', this.pdfDoc.numPages);
      
      // Setup canvas and render first page
      console.log('DEBUG: Setting up canvas');
      this.setupCanvas();
      console.log('DEBUG: Rendering first page');
      await this.renderPage(1);
      console.log('DEBUG: First page rendered');
      
      return true;
    } catch (error) {
      console.error('ERROR in loadDocument:', error);
      console.error('Error details:', error.message);
      console.error('Error stack:', error.stack);
      throw error;
    }
  }

  setupCanvas() {
    this.canvas = document.getElementById('pdf-canvas');
    this.context = this.canvas.getContext('2d');
    this.highlightOverlay = document.getElementById('citation-highlights-overlay');
    
    // Update page info
    const totalPagesEl = document.getElementById('total-pages');
    if (totalPagesEl && this.pdfDoc) {
      totalPagesEl.textContent = this.pdfDoc.numPages;
    }
  }

  async renderPage(pageNumber) {
    try {
      const page = await this.pdfDoc.getPage(pageNumber);
      const viewport = page.getViewport({ scale: this.zoomLevel });
      
      // Set canvas dimensions
      this.canvas.height = viewport.height;
      this.canvas.width = viewport.width;
      
      // Render PDF page
      const renderContext = {
        canvasContext: this.context,
        viewport: viewport
      };
      
      await page.render(renderContext).promise;
      
      // Update current page
      this.currentPage = pageNumber;
      const currentPageInput = document.getElementById('current-page-input');
      if (currentPageInput) {
        currentPageInput.value = pageNumber;
      }
      
      // Highlight citations on this page
      this.highlightCitationsOnPage(pageNumber);
      
    } catch (error) {
      console.error('Error rendering page:', error);
    }
  }

  highlightCitationsOnPage(pageNumber) {
    // Clear existing highlights
    if (this.highlightOverlay) {
      this.highlightOverlay.innerHTML = '';
    }
    
    // Find citations for current page
    const pageCitations = this.citations.filter(citation => 
      citation.pageNumber === pageNumber
    );
    
    // For now, create simple highlighting boxes
    // This will be enhanced in Phase 3 with actual bounding boxes
    pageCitations.forEach((citation, index) => {
      if (this.highlightOverlay) {
        const highlight = document.createElement('div');
        highlight.className = `citation-highlight citation-${index}`;
        highlight.style.position = 'absolute';
        highlight.style.left = '50px';
        highlight.style.top = `${100 + (index * 60)}px`;
        highlight.style.width = '200px';
        highlight.style.height = '40px';
        highlight.style.backgroundColor = 'rgba(255, 255, 0, 0.3)';
        highlight.style.border = '2px solid #ffa500';
        highlight.style.borderRadius = '2px';
        highlight.style.cursor = 'pointer';
        highlight.title = citation.textContent.substring(0, 100) + '...';
        
        highlight.addEventListener('click', () => {
          this.showCitationTooltip(citation, highlight);
        });
        
        this.highlightOverlay.appendChild(highlight);
      }
    });
  }

  showCitationTooltip(citation, element) {
    // Show a tooltip with citation text
    const tooltip = document.createElement('div');
    tooltip.className = 'citation-tooltip';
    tooltip.style.position = 'absolute';
    tooltip.style.background = 'rgba(0,0,0,0.9)';
    tooltip.style.color = 'white';
    tooltip.style.padding = '10px';
    tooltip.style.borderRadius = '5px';
    tooltip.style.maxWidth = '300px';
    tooltip.style.zIndex = '1000';
    tooltip.style.fontSize = '14px';
    tooltip.textContent = citation.textContent;
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = `${rect.right + 10}px`;
    tooltip.style.top = `${rect.top}px`;
    
    document.body.appendChild(tooltip);
    
    // Remove tooltip after 3 seconds or on click
    setTimeout(() => {
      if (tooltip.parentNode) {
        tooltip.parentNode.removeChild(tooltip);
      }
    }, 3000);
    
    tooltip.addEventListener('click', () => {
      if (tooltip.parentNode) {
        tooltip.parentNode.removeChild(tooltip);
      }
    });
  }

  async navigateToCitation(citationIndex) {
    if (citationIndex < 0 || citationIndex >= this.citations.length) {
      return;
    }
    
    this.currentCitationIndex = citationIndex;
    const citation = this.citations[citationIndex];
    
    // Navigate to citation page
    await this.renderPage(citation.pageNumber);
    
    // Update navigation UI
    this.updateNavigationUI();
  }

  updateNavigationUI() {
    const prevBtn = document.getElementById('prev-citation');
    const nextBtn = document.getElementById('next-citation');
    const counter = document.querySelector('.citation-counter');
    
    if (prevBtn) {
      prevBtn.disabled = this.currentCitationIndex === 0;
    }
    
    if (nextBtn) {
      nextBtn.disabled = this.currentCitationIndex === this.citations.length - 1;
    }
    
    if (counter) {
      counter.textContent = `Citation ${this.currentCitationIndex + 1} of ${this.citations.length} | Page ${this.currentPage} of ${this.pdfDoc ? this.pdfDoc.numPages : 1}`;
    }
  }

  setupEventListeners() {
    // Page navigation
    const prevPageBtn = document.getElementById('pdf-prev-page');
    const nextPageBtn = document.getElementById('pdf-next-page');
    const currentPageInput = document.getElementById('current-page-input');
    
    if (prevPageBtn) {
      prevPageBtn.addEventListener('click', async () => {
        if (this.currentPage > 1) {
          await this.renderPage(this.currentPage - 1);
        }
      });
    }
    
    if (nextPageBtn) {
      nextPageBtn.addEventListener('click', async () => {
        if (this.pdfDoc && this.currentPage < this.pdfDoc.numPages) {
          await this.renderPage(this.currentPage + 1);
        }
      });
    }
    
    if (currentPageInput) {
      currentPageInput.addEventListener('change', async (e) => {
        const pageNum = parseInt(e.target.value);
        if (pageNum >= 1 && pageNum <= (this.pdfDoc ? this.pdfDoc.numPages : 1)) {
          await this.renderPage(pageNum);
        }
      });
    }
    
    // Citation navigation
    const prevCitationBtn = document.getElementById('prev-citation');
    const nextCitationBtn = document.getElementById('next-citation');
    
    if (prevCitationBtn) {
      prevCitationBtn.addEventListener('click', () => {
        if (this.currentCitationIndex > 0) {
          this.navigateToCitation(this.currentCitationIndex - 1);
        }
      });
    }
    
    if (nextCitationBtn) {
      nextCitationBtn.addEventListener('click', () => {
        if (this.currentCitationIndex < this.citations.length - 1) {
          this.navigateToCitation(this.currentCitationIndex + 1);
        }
      });
    }
    
    // Zoom controls
    const zoomInBtn = document.getElementById('zoom-in');
    const zoomOutBtn = document.getElementById('zoom-out');
    const zoomFitBtn = document.getElementById('zoom-fit');
    
    if (zoomInBtn) {
      zoomInBtn.addEventListener('click', () => {
        this.zoomLevel = Math.min(this.zoomLevel * 1.2, 3.0);
        this.renderPage(this.currentPage);
        this.updateZoomLevel();
      });
    }
    
    if (zoomOutBtn) {
      zoomOutBtn.addEventListener('click', () => {
        this.zoomLevel = Math.max(this.zoomLevel / 1.2, 0.5);
        this.renderPage(this.currentPage);
        this.updateZoomLevel();
      });
    }
    
    if (zoomFitBtn) {
      zoomFitBtn.addEventListener('click', () => {
        this.zoomLevel = 1.0;
        this.renderPage(this.currentPage);
        this.updateZoomLevel();
      });
    }
  }

  updateZoomLevel() {
    const zoomLevelEl = document.getElementById('zoom-level');
    if (zoomLevelEl) {
      zoomLevelEl.textContent = Math.round(this.zoomLevel * 100) + '%';
    }
  }

  dispose() {
    if (this.pdfDoc) {
      this.pdfDoc.destroy();
    }
  }
}

/**
 * Fetch all citations for a document
 */
async function fetchAllDocumentCitations(docId, fileName = '') {
  try {
    const response = await fetch('/api/get_document_citations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        document_id: docId,
        file_name: fileName
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching document citations:', error);
    throw error;
  }
}

/**
 * Create the enhanced PDF modal HTML structure
 */
function createEnhancedPdfModal() {
  const existingModal = document.getElementById('citation-pdf-modal');
  if (existingModal) {
    existingModal.remove();
  }
  
  const modal = document.createElement('div');
  modal.id = 'citation-pdf-modal';
  modal.className = 'modal fade citation-pdf-modal';
  modal.tabIndex = -1;
  modal.setAttribute('aria-labelledby', 'citationPdfModalLabel');
  modal.setAttribute('aria-hidden', 'true');
  
  modal.innerHTML = `
    <div class="modal-dialog modal-fullscreen-lg">
      <div class="modal-content">
        <div class="modal-header">
          <div class="citation-nav-info">
            <h5 class="modal-title" id="citationPdfModalLabel">Document Viewer</h5>
            <div class="citation-counter">Loading...</div>
          </div>
          <div class="citation-controls">
            <button type="button" class="btn btn-sm btn-outline-secondary" id="prev-citation">
              <i class="bi bi-chevron-left"></i> Previous Citation
            </button>
            <button type="button" class="btn btn-sm btn-outline-secondary" id="next-citation">
              Next Citation <i class="bi bi-chevron-right"></i>
            </button>
          </div>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        
        <div class="modal-body p-0">
          <div class="pdf-viewer-container">
            <div id="pdf-canvas-container" class="pdf-canvas-wrapper">
              <canvas id="pdf-canvas"></canvas>
              <div id="citation-highlights-overlay" class="citation-highlights"></div>
            </div>
            
            <div class="pdf-controls-overlay">
              <div class="pdf-navigation">
                <button type="button" id="pdf-prev-page" class="btn btn-sm btn-secondary">
                  <i class="bi bi-chevron-left"></i>
                </button>
                <span class="page-info">
                  <input type="number" id="current-page-input" min="1" value="1" class="form-control form-control-sm">
                  <span>of <span id="total-pages">1</span></span>
                </span>
                <button type="button" id="pdf-next-page" class="btn btn-sm btn-secondary">
                  <i class="bi bi-chevron-right"></i>
                </button>
              </div>
              
              <div class="pdf-zoom-controls">
                <button type="button" id="zoom-out" class="btn btn-sm btn-secondary">
                  <i class="bi bi-zoom-out"></i>
                </button>
                <span id="zoom-level">100%</span>
                <button type="button" id="zoom-in" class="btn btn-sm btn-secondary">
                  <i class="bi bi-zoom-in"></i>
                </button>
                <button type="button" id="zoom-fit" class="btn btn-sm btn-secondary">Fit Width</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  return modal;
}

/**
 * Show enhanced PDF modal with citation highlighting
 */
export async function showEnhancedPdfModal(docId, citationId, allCitations = null) {
  console.log('DEBUG: Starting showEnhancedPdfModal', { docId, citationId, allCitations });
  
  try {
    showLoadingIndicator();
    console.log('DEBUG: Loading indicator shown');
    
    // Create enhanced modal structure
    console.log('DEBUG: Creating enhanced modal structure');
    const modal = createEnhancedPdfModal();
    console.log('DEBUG: Modal created successfully');
    
    // Load document and citation data
    console.log('DEBUG: Loading citation data');
    const citationData = allCitations || await fetchAllDocumentCitations(docId);
    console.log('DEBUG: Citation data loaded:', citationData);
    
    // Check if PDF.js is available
    if (typeof pdfjsLib === 'undefined') {
      throw new Error('PDF.js library not loaded');
    }
    
    // Initialize PDF viewer
    console.log('DEBUG: Initializing PDF viewer');
    const viewer = new EnhancedPDFCitationViewer('citation-pdf-modal');
    console.log('DEBUG: PDF viewer created, loading document');
    await viewer.loadDocument(docId, citationData);
    console.log('DEBUG: Document loaded successfully');
    
    // Setup event listeners
    console.log('DEBUG: Setting up event listeners');
    viewer.setupEventListeners();
    
    // Navigate to specific citation
    const citationIndex = citationData.citations.findIndex(c => c.citationId === citationId);
    console.log('DEBUG: Citation index found:', citationIndex);
    if (citationIndex >= 0) {
      await viewer.navigateToCitation(citationIndex);
      console.log('DEBUG: Navigated to citation');
    }
    
    // Show modal
    console.log('DEBUG: Showing modal');
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    // Cleanup on modal close
    modal.addEventListener('hidden.bs.modal', () => {
      console.log('DEBUG: Modal closing, disposing viewer');
      viewer.dispose();
      modal.remove();
    });
    
    hideLoadingIndicator();
    console.log('DEBUG: Enhanced PDF modal shown successfully');
    
  } catch (error) {
    console.error('ERROR in showEnhancedPdfModal:', error);
    console.error('Error stack:', error.stack);
    hideLoadingIndicator();
    showToast('Failed to load enhanced PDF viewer. Falling back to text citation.', 'warning');
    
    // Fallback to text citation
    fetchCitedText(citationId);
  }
}

/**
 * Progressive enhancement function - tries enhanced viewer first, falls back as needed
 */
export async function showCitationWithFallback(citationId, docId) {
  // Check if PDF.js is available and enhanced citations are enabled
  if (typeof pdfjsLib !== 'undefined' && window.enableEnhancedCitations) {
    try {
      await showEnhancedPdfModal(docId, citationId);
      return;
    } catch (error) {
      console.warn('Enhanced PDF viewer failed:', error);
    }
  }
  
  // Try basic PDF modal
  try {
    const { pageNumber } = parseDocIdAndPage(citationId);
    await showPdfModal(docId, pageNumber, citationId);
    return;
  } catch (error) {
    console.warn('Basic PDF viewer failed:', error);
  }
  
  // Final fallback to text citation
  fetchCitedText(citationId);
}

// ---------------------------------------