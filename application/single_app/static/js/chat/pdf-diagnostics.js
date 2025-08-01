// Enhanced PDF Citation Viewer Diagnostics
// Add this to browser console to diagnose environment issues

window.diagnoseCitationEnvironment = function() {
    console.log('=== ENHANCED PDF CITATION DIAGNOSTICS ===');
    
    // 1. PDF.js Library Check
    console.log('\n1. PDF.js Library Status:');
    console.log('PDF.js loaded:', typeof pdfjsLib !== 'undefined');
    if (typeof pdfjsLib !== 'undefined') {
        console.log('PDF.js version:', pdfjsLib.version || 'Unknown');
        console.log('Worker path configured:', pdfjsLib.GlobalWorkerOptions.workerSrc);
        
        // Test worker access
        try {
            const testUrl = '/static/js/lib/pdfjs/pdf.worker.min.js';
            fetch(testUrl, { method: 'HEAD' })
                .then(response => {
                    console.log('Worker file accessible:', response.ok, 'Status:', response.status);
                })
                .catch(err => {
                    console.error('Worker file test failed:', err);
                });
        } catch (err) {
            console.error('Worker test error:', err);
        }
    } else {
        console.error('PDF.js library not loaded!');
        
        // Check if script tag exists
        const pdfScript = document.querySelector('script[src*="pdf.min.js"]');
        console.log('PDF.js script tag found:', !!pdfScript);
        if (pdfScript) {
            console.log('Script src:', pdfScript.src);
        }
    }
    
    // 2. Environment Detection
    console.log('\n2. Environment Detection:');
    console.log('User Agent:', navigator.userAgent);
    console.log('Current URL:', window.location.href);
    console.log('Protocol:', window.location.protocol);
    console.log('Host:', window.location.host);
    
    // Check if running in deployed environment
    const isProduction = window.location.hostname !== 'localhost' && 
                        window.location.hostname !== '127.0.0.1' && 
                        !window.location.hostname.includes('dev');
    console.log('Likely production environment:', isProduction);
    
    // 3. Enhanced Citations Settings
    console.log('\n3. Enhanced Citations Configuration:');
    console.log('Enhanced citations enabled globally:', window.enableEnhancedCitations);
    
    // 4. Network Connectivity Tests
    console.log('\n4. Network Connectivity Tests:');
    
    // Test basic connectivity
    const testUrls = [
        '/static/js/lib/pdfjs/pdf.min.js',
        '/static/js/lib/pdfjs/pdf.worker.min.js',
        '/api/get_citation', // Basic API test
    ];
    
    testUrls.forEach(url => {
        fetch(url, { method: 'HEAD' })
            .then(response => {
                console.log(`${url}: Status ${response.status} (${response.ok ? 'OK' : 'FAILED'})`);
            })
            .catch(err => {
                console.error(`${url}: FAILED -`, err.message);
            });
    });
    
    // 5. Test Document Endpoint with Sample ID
    console.log('\n5. Document Endpoint Test:');
    const sampleDocId = '29f51880-6bd6-42b3-9df5-fe98802b72bf'; // Use the failing ID from your error
    const docUrl = `/view_document/${sampleDocId}`;
    
    // First test the diagnostic endpoint
    const debugUrl = `/api/debug/document_access/${sampleDocId}`;
    fetch(debugUrl)
        .then(response => response.json())
        .then(data => {
            console.log('Server-side diagnostics:', data);
            if (data.checks) {
                console.log('Document metadata accessible:', data.checks.document_metadata?.accessible);
                console.log('Storage configured:', data.checks.storage_config?.all_configured);
                console.log('Enhanced citations enabled:', data.checks.enhanced_citations?.enabled);
            }
        })
        .catch(err => {
            console.error('Server diagnostics failed:', err);
        });
    
    fetch(docUrl, { method: 'HEAD' })
        .then(response => {
            console.log(`Document endpoint test: Status ${response.status}`);
            if (!response.ok) {
                console.error('Document endpoint failed. This is likely the main issue.');
                console.log('Response headers:', [...response.headers.entries()]);
            }
        })
        .catch(err => {
            console.error('Document endpoint test failed:', err);
        });
    
    // 6. Check for Azure/Authentication Issues
    console.log('\n6. Authentication & Azure Status:');
    fetch('/api/get_citation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ citation_id: 'test' })
    })
    .then(response => {
        console.log('API authentication test status:', response.status);
        if (response.status === 401) {
            console.error('Authentication issue detected!');
        } else if (response.status === 500) {
            console.error('Server error detected!');
        }
    })
    .catch(err => {
        console.error('API test failed:', err);
    });
    
    // 7. Browser Capabilities
    console.log('\n7. Browser Capabilities:');
    console.log('Canvas support:', !!document.createElement('canvas').getContext);
    console.log('Fetch API support:', typeof fetch !== 'undefined');
    console.log('Promise support:', typeof Promise !== 'undefined');
    console.log('WebWorker support:', typeof Worker !== 'undefined');
    
    // 8. Security Context
    console.log('\n8. Security Context:');
    console.log('HTTPS:', window.location.protocol === 'https:');
    console.log('Secure context:', window.isSecureContext);
    
    // Check Content Security Policy
    const metaCSP = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
    if (metaCSP) {
        console.log('CSP meta tag found:', metaCSP.content);
    } else {
        console.log('No CSP meta tag found');
    }
    
    console.log('\n=== DIAGNOSTICS COMPLETE ===');
    console.log('If PDF.js is not loading, check:');
    console.log('1. Network connectivity to local PDF.js files');
    console.log('2. Server configuration for static file serving');
    console.log('3. Content Security Policy settings');
    console.log('4. Document endpoint authentication and Azure Storage');
    
    return {
        pdfJsLoaded: typeof pdfjsLib !== 'undefined',
        environment: isProduction ? 'production' : 'development',
        enhancedEnabled: window.enableEnhancedCitations,
        workerConfigured: typeof pdfjsLib !== 'undefined' && !!pdfjsLib.GlobalWorkerOptions.workerSrc
    };
};

// Auto-run diagnostics if there are PDF viewer issues
if (typeof pdfjsLib === 'undefined') {
    console.warn('PDF.js not detected. Run window.diagnoseCitationEnvironment() for diagnostics.');
}
