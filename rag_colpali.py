import requests
import html
import re
import textwrap

class ColPaliRAG:
    def __init__(self, api_url: str):
        if not api_url.startswith("https://"):
            raise ValueError("Invalid ngrok URL. It must start with 'https://'")
        self.api_url = api_url.rstrip('/')
        # Test the connection to the API server
        response = requests.get(self.api_url)
        response.raise_for_status() # This will raise an error if the connection fails

    def query(self, query_text: str,chat_history: list = None):
        """Sends the query and chat history to the Colab API."""
        endpoint = f"{self.api_url}/query"
        payload = {"query_text": query_text, "chat_history": chat_history or []}
        
        response = requests.post(endpoint, json=payload, timeout=120) # 2-minute timeout
        response.raise_for_status() # Raise an error for bad responses
        
        return response.json()

    def build_citation_html(self, answer: str, retrieved_docs: list) -> str:
        """Build HTML with pure CSS hover tooltips - Shows only the answer with citations"""
        
        # Create a lookup dictionary for citations
        citation_lookup = {doc['citation']: doc for doc in retrieved_docs}
        
        # Escape answer text first
        escaped_answer = html.escape(answer).replace("\n", "<br>")
        
        # First pass: collect ALL citation numbers from the text
        all_citation_nums = set(int(match.group(1)) for match in re.finditer(r'\[(\d+)\]', escaped_answer))
        
        # Generate CSS for ALL citations that appear in the text
        css_styles = []
        for citation_num in sorted(all_citation_nums):
            if citation_num not in citation_lookup:
                continue
                
            hover_class = f"cite-{citation_num}"
            tooltip_class = f"tooltip-{citation_num}"
            
            css = f"""
            .{hover_class} {{
                color: #60a5fa;
                cursor: pointer;
                font-weight: 600;
                border-bottom: 2px solid rgba(96,165,250,0.3);
                padding: 0 2px;
                position: relative;
                display: inline-block;
            }}
            .{hover_class}:hover {{
                background-color: rgba(96,165,250,0.1);
                border-bottom-color: #60a5fa;
            }}
            .{tooltip_class} {{
                visibility: hidden;
                opacity: 0;
                position: fixed;
                z-index: 9999;
                left: 50%;
                top: 50%;
                transform: translate(-50%, -50%);
                width: 450px;
                max-width: 90vw;
                background-color: #2d3748;
                color: #e6eef8;
                padding: 16px;
                border-radius: 8px;
                border: 1px solid #0f172a;
                box-shadow: 0 8px 24px rgba(2,6,23,0.45);
                transition: opacity 0.3s, visibility 0.3s;
                font-size: 13px;
                font-weight: normal;
                text-align: left;
                white-space: normal;
                pointer-events: none;
                max-height: 80vh;
                overflow-y: auto;
            }}
            .{hover_class}:hover .{tooltip_class} {{
                visibility: visible;
                opacity: 1;
            }}
            """
            css_styles.append(css)
        
        # Replace citations with styled spans
        def replace_citation(match):
            citation_num = int(match.group(1))
            if citation_num not in citation_lookup:
                return match.group(0)  # Return original if not found
            
            hover_class = f"cite-{citation_num}"
            tooltip_class = f"tooltip-{citation_num}"
            
            doc = citation_lookup[citation_num]
            tooltip_header = f"Page {doc.get('page_number')} (Score: {doc.get('score', 0):.3f})"
            tooltip_text = html.escape(doc.get('excerpt', '')[:400])
            thumbnail_b64 = doc.get('thumbnail', '')
            
            img_html = f'<img src="data:image/png;base64,{thumbnail_b64}" style="margin-top:12px;width:100%;max-width:300px;height:auto;border:1px solid #4a5568;border-radius:4px;display:block;" />' if thumbnail_b64 else ''
            
            return f"""<span class="{hover_class}">[{citation_num}]<span class="{tooltip_class}"><div style="font-weight:bold;margin-bottom:10px;font-size:14px;color:#60a5fa;">{tooltip_header}</div><div style="margin-top:8px;line-height:1.5;color:#cbd5e0;">{tooltip_text}</div>{img_html}</span></span>"""
        
        # Replace all citations in the text
        html_with_citations = re.sub(r'\[(\d+)\]', replace_citation, escaped_answer)
        
        # Build final HTML - Only show the answer with citations
        all_css = '\n'.join(css_styles)
        
        final_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        {all_css}
        body {{
            margin: 0;
            padding: 0;
            overflow: visible;
        }}
        #rag-answer-wrapper {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #e6eef8;
            line-height: 1.6;
            padding: 10px;
            min-height: fit-content;
        }}
        #answer-text {{
            background: transparent;
            padding: 0;
            margin: 0;
        }}
        </style>
        </head>
        <body>
        <div id="rag-answer-wrapper">
            <div id="answer-text">
                {html_with_citations}
            </div>
        </div>
        <script>
            // Auto-resize to fit content
            function resizeIframe() {{
                const height = document.body.scrollHeight;
                window.parent.postMessage({{
                    type: 'streamlit:setFrameHeight',
                    height: height + 20
                }}, '*');
            }}
            
            // Initial resize
            resizeIframe();
            
            // Resize on window load and resize
            window.addEventListener('load', resizeIframe);
            window.addEventListener('resize', resizeIframe);
            
            // Observe DOM changes for dynamic content
            const observer = new MutationObserver(resizeIframe);
            observer.observe(document.body, {{
                childList: true,
                subtree: true,
                attributes: true
            }});
        </script>
        </body>
        </html>
        """
        
        return final_html