"""
Fixed RAG Extensions Module - Mind Map Generation
Corrected positioning, scaling, and rendering issues
"""

import json
import re
from collections import Counter


class RAGExtensions:
    def __init__(self, rag_instance):
        """Initialize extensions with existing RAG instance."""
        self.rag = rag_instance
        self.structure = None
        print("✅ RAG Extensions initialized")

    def _find_keyword_locations(self, keyword):
        """Find all pages where a keyword appears."""
        locations = []
        keyword_lower = keyword.lower()
        payloads = getattr(self.rag, 'payloads', {})
        
        for payload in payloads.values():
            ocr_text = payload.get('ocr_text', '').lower()
            if keyword_lower in ocr_text:
                idx = ocr_text.find(keyword_lower)
                start = max(0, idx - 75)
                end = idx + len(keyword) + 75
                context = f"...{payload.get('ocr_text', '')[start:end].replace(chr(10), ' ')}..."
                locations.append({
                    'page_number': payload.get('page_number', 'N/A'),
                    'context': context,
                    'page_image': payload.get('page_base64_image', '')
                })
        return sorted(locations, key=lambda x: x.get('page_number') or 0)

    def _extract_important_points(self):
        """Extract the most important points from the document using AI."""
        print("🔍 Extracting important points from document...")
        payloads = getattr(self.rag, 'payloads', None)
        
        if not payloads:
            print("❌ No payloads found")
            return None

        all_pages = sorted(payloads.values(), key=lambda x: x.get('page_number', 0))
        full_text = "\n\n".join(p.get('ocr_text', '') for p in all_pages[:30])
        
        if len(full_text) > 20000:
            full_text = full_text[:20000]
        
        extraction_prompt = f'''Analyze the document text to identify its core structure. Return ONLY a JSON object with this schema:
{{
  "document_title": "string",
  "key_points": [
    {{
      "title": "string",
      "description": "string",
      "subtopics": ["string"]
    }}
  ]
}}

Rules:
- "key_points" should be 5-8 main topics
- "subtopics" should be 2-4 crucial details per point
- Keep titles concise (max 60 characters)

Text: {full_text}'''
        
        try:
            response = self.rag.model.generate_content(
                extraction_prompt,
                generation_config={
                    "temperature": 0.1,
                    "response_mime_type": "application/json"
                }
            )
            structure = json.loads(response.text)
            print(f"✅ Extracted {len(structure.get('key_points', []))} key points")
            return structure
        except Exception as e:
            print(f"⚠️ AI extraction failed: {e}")
            return None

    def generate_mind_map(self):
        """Generate the complete HTML for an interactive mind map."""
        structure = self._extract_important_points()
        if not structure:
            return "<div>Failed to generate structure.</div>"

        print("🎨 Building organized mind map...")
        
        nodes, edges = [], []
        root_title = structure.get("document_title", "Document").strip() or "Document"
        nodes.append({
            "id": "root",
            "label": root_title,
            "level": 0,
            "type": "root",
            "keyword": root_title,
            "description": f"Analysis of {root_title}"
        })
        
        for i, kp in enumerate(structure.get("key_points", [])):
            kp_id = f"kp_{i}"
            kp_title = kp.get("title", f"Point {i+1}").strip()
            if not kp_title:
                continue
                
            nodes.append({
                "id": kp_id,
                "label": kp_title,
                "level": 1,
                "type": "keypoint",
                "description": kp.get("description", ""),
                "keyword": kp_title
            })
            edges.append({"from": "root", "to": kp_id})
            
            for j, st in enumerate(kp.get("subtopics", [])[:4]):
                st_title = st.strip()
                if not st_title:
                    continue
                st_id = f"st_{i}_{j}"
                nodes.append({
                    "id": st_id,
                    "label": st_title,
                    "level": 2,
                    "type": "subtopic",
                    "description": f"Detail of {kp_title}",
                    "keyword": st_title
                })
                edges.append({"from": kp_id, "to": st_id})
        
        location_data = {
            n['id']: self._find_keyword_locations(n['keyword']) 
            for n in nodes if n.get('keyword')
        }
        
        print(f"✅ Mind map ready with {len(nodes)} nodes")
        return self._generate_mindmap_html(nodes, edges, location_data)

    def _generate_mindmap_html(self, nodes, edges, location_data):
        """Generate the complete HTML for the mind map visualization."""
        nodes_json = json.dumps(nodes)
        edges_json = json.dumps(edges)
        location_json = json.dumps(location_data)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e14;
            color: #fff;
            overflow: hidden;
        }}
        #mindmap-container {{
            width: 100vw;
            height: 100vh;
            position: relative;
            background: radial-gradient(circle at center, #1a1f2e 0%, #0f1419 100%);
        }}
        #canvas {{
            width: 100%;
            height: 100%;
            position: relative;
            overflow: hidden;
            cursor: grab;
        }}
        #canvas:active {{ cursor: grabbing; }}
        
        .node {{
            position: absolute;
            padding: 12px 20px;
            background: #1e2530;
            border: 2px solid #374151;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 14px;
            white-space: nowrap;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
            display: flex;
            align-items: center;
            gap: 10px;
            color: #e5e7eb;
            user-select: none;
        }}
        
        .node:hover {{
            transform: scale(1.05);
            border-color: #4a9eff;
            z-index: 1000;
            box-shadow: 0 6px 20px rgba(74, 158, 255, 0.4);
        }}
        
        .node.root {{
            background: linear-gradient(145deg, #1e40af, #3b82f6);
            border-color: #60a5fa;
            font-size: 18px;
            font-weight: 700;
            padding: 16px 28px;
        }}
        
        .node.keypoint {{
            background: linear-gradient(135deg, #1e2530, #252d3d);
            border-color: #4a9eff;
            font-weight: 600;
        }}
        
        .node.subtopic {{
            background: #1a1f2e;
            border-color: #374151;
            font-size: 13px;
            padding: 10px 16px;
        }}
        
        .expand-icon {{
            width: 20px;
            height: 20px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #374151;
            border-radius: 5px;
            font-size: 13px;
            font-weight: bold;
            color: #9ca3af;
            flex-shrink: 0;
        }}
        
        .expand-icon.collapsed::after {{ content: '+'; }}
        .expand-icon.expanded::after {{ content: '−'; }}
        .expand-icon.leaf {{ background: transparent; }}
        
        svg {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
        }}
        
        .edge {{
            stroke: #4a5568;
            stroke-width: 2;
            fill: none;
            opacity: 0.7;
        }}
        
        .controls {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 2000;
            display: flex;
            gap: 10px;
        }}
        
        .btn {{
            padding: 10px 18px;
            background: #252d3d;
            border: 1px solid #374151;
            color: #e5e7eb;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }}
        
        .btn:hover {{
            background: #2d3548;
            border-color: #4a9eff;
        }}
        
        .info-panel {{
            position: absolute;
            top: 20px;
            right: 20px;
            width: 380px;
            max-height: calc(100vh - 40px);
            background: rgba(30, 41, 59, 0.95);
            backdrop-filter: blur(8px);
            border: 1px solid #374151;
            border-radius: 10px;
            padding: 20px;
            overflow-y: auto;
            display: none;
            z-index: 2000;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }}
        
        .info-panel h3 {{
            color: #60a5fa;
            margin-bottom: 12px;
            font-size: 18px;
        }}
        
        .info-panel p {{
            color: #d1d5db;
            line-height: 1.6;
            margin-bottom: 16px;
        }}
        
        .location-item {{
            margin-top: 15px;
            padding: 12px;
            background: #1a1f2e;
            border-radius: 6px;
            border-left: 3px solid #4a9eff;
            font-size: 13px;
        }}
        
        .location-item strong {{
            color: #60a5fa;
            display: block;
            margin-bottom: 8px;
        }}
        
        .location-item p {{
            color: #9ca3af;
            margin: 0;
            font-size: 12px;
        }}
        
        .location-item img {{
            width: 100%;
            border-radius: 4px;
            margin-top: 8px;
        }}
    </style>
</head>
<body>
    <div id="mindmap-container">
        <div class="controls">
            <button class="btn" onclick="expandAll()">Expand All</button>
            <button class="btn" onclick="collapseAll()">Collapse All</button>
            <button class="btn" onclick="resetView()">Reset View</button>
        </div>
        <div class="info-panel" id="info-panel"></div>
        <div id="canvas">
            <svg id="edges"></svg>
            <div id="nodes-container"></div>
        </div>
    </div>
    
    <script>
        const nodesData = {nodes_json};
        const edgesData = {edges_json};
        const locationData = {location_json};
        
        let positions = {{}};
        let scale = 1;
        let offsetX = 0;
        let offsetY = 0;
        let collapsedNodes = new Set();
        
        // Initialize - collapse all except root
        nodesData.forEach(n => {{
            if (n.level > 0) collapsedNodes.add(n.id);
        }});
        
        function getChildrenIds(nodeId) {{
            return edgesData.filter(e => e.from === nodeId).map(e => e.to);
        }}
        
        function isNodeVisible(nodeId) {{
            const edge = edgesData.find(e => e.to === nodeId);
            if (!edge) return true;
            if (collapsedNodes.has(edge.from)) return false;
            return isNodeVisible(edge.from);
        }}
        
        function calculateLayout() {{
            const centerX = window.innerWidth / 2;
            const centerY = window.innerHeight / 2;
            
            // Root at center
            positions['root'] = {{ x: centerX, y: centerY }};
            
            // Level 1 nodes in circle
            const level1Nodes = nodesData.filter(n => n.level === 1);
            const level1Count = level1Nodes.length;
            const level1Radius = Math.min(centerX, centerY) * 0.5;
            
            level1Nodes.forEach((node, i) => {{
                const angle = (i * 2 * Math.PI / level1Count) - Math.PI / 2;
                positions[node.id] = {{
                    x: centerX + level1Radius * Math.cos(angle),
                    y: centerY + level1Radius * Math.sin(angle)
                }};
            }});
            
            // Level 2 nodes around their parents
            const level2Radius = Math.min(centerX, centerY) * 0.8;
            
            level1Nodes.forEach(parentNode => {{
                const children = edgesData
                    .filter(e => e.from === parentNode.id)
                    .map(e => e.to);
                
                if (children.length === 0) return;
                
                const parentPos = positions[parentNode.id];
                const parentAngle = Math.atan2(
                    parentPos.y - centerY,
                    parentPos.x - centerX
                );
                
                const spread = Math.PI / 4;
                const startAngle = parentAngle - spread / 2;
                
                children.forEach((childId, i) => {{
                    const angle = startAngle + (children.length > 1 
                        ? (i / (children.length - 1)) * spread 
                        : 0);
                    
                    positions[childId] = {{
                        x: centerX + level2Radius * Math.cos(angle),
                        y: centerY + level2Radius * Math.sin(angle)
                    }};
                }});
            }});
        }}
        
        function render() {{
            const nodesContainer = document.getElementById('nodes-container');
            const edgesSvg = document.getElementById('edges');
            
            nodesContainer.innerHTML = '';
            edgesSvg.innerHTML = '';
            
            // Render edges
            edgesData.forEach(edge => {{
                if (!isNodeVisible(edge.to)) return;
                
                const fromPos = positions[edge.from];
                const toPos = positions[edge.to];
                
                if (!fromPos || !toPos) return;
                
                const x1 = fromPos.x * scale + offsetX;
                const y1 = fromPos.y * scale + offsetY;
                const x2 = toPos.x * scale + offsetX;
                const y2 = toPos.y * scale + offsetY;
                
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('class', 'edge');
                path.setAttribute('d', `M ${{x1}},${{y1}} L ${{x2}},${{y2}}`);
                edgesSvg.appendChild(path);
            }});
            
            // Render nodes
            nodesData.forEach(node => {{
                if (!isNodeVisible(node.id)) return;
                
                const pos = positions[node.id];
                if (!pos) return;
                
                const nodeEl = document.createElement('div');
                nodeEl.className = `node ${{node.type}}`;
                nodeEl.onclick = () => showNodeInfo(node.id);
                
                const children = getChildrenIds(node.id);
                
                const icon = document.createElement('span');
                icon.className = `expand-icon ${{
                    children.length > 0 
                        ? (collapsedNodes.has(node.id) ? 'collapsed' : 'expanded')
                        : 'leaf'
                }}`;
                
                if (children.length > 0) {{
                    icon.onclick = (e) => {{
                        e.stopPropagation();
                        toggleNodeCollapse(node.id);
                    }};
                }}
                
                const label = document.createElement('span');
                label.textContent = node.label;
                
                nodeEl.appendChild(icon);
                nodeEl.appendChild(label);
                
                nodeEl.style.left = `${{pos.x * scale + offsetX}}px`;
                nodeEl.style.top = `${{pos.y * scale + offsetY}}px`;
                nodeEl.style.transform = 'translate(-50%, -50%)';
                
                nodesContainer.appendChild(nodeEl);
            }});
        }}
        
        function toggleNodeCollapse(nodeId) {{
            if (collapsedNodes.has(nodeId)) {{
                collapsedNodes.delete(nodeId);
            }} else {{
                collapsedNodes.add(nodeId);
            }}
            render();
        }}
        
        function expandAll() {{
            collapsedNodes.clear();
            render();
        }}
        
        function collapseAll() {{
            nodesData.forEach(n => {{
                if (n.level > 0) collapsedNodes.add(n.id);
            }});
            render();
        }}
        
        function showNodeInfo(nodeId) {{
            const node = nodesData.find(n => n.id === nodeId);
            if (!node) return;
            
            const panel = document.getElementById('info-panel');
            let html = `<h3>${{node.label}}</h3><p>${{node.description || ''}}</p>`;
            
            const locations = locationData[nodeId];
            if (locations && locations.length > 0) {{
                html += `<h4 style="color: #9ca3af; margin: 20px 0 10px 0;">Found in ${{locations.length}} page(s):</h4>`;
                locations.forEach(loc => {{
                    html += `<div class="location-item">
                        <strong>Page ${{loc.page_number}}</strong>
                        <p>${{loc.context}}</p>`;
                    if (loc.page_image) {{
                        html += `<img src="data:image/png;base64,${{loc.page_image}}">`;
                    }}
                    html += '</div>';
                }});
            }}
            
            panel.innerHTML = html;
            panel.style.display = 'block';
        }}
        
        function resetView() {{
            scale = 1;
            offsetX = 0;
            offsetY = 0;
            render();
        }}
        
        // Pan & Zoom Controls
        const canvas = document.getElementById('canvas');
        let isDragging = false;
        let startX = 0;
        let startY = 0;
        let initialOffsetX = 0;
        let initialOffsetY = 0;
        
        canvas.addEventListener('mousedown', (e) => {{
            if (e.target !== canvas && 
                e.target.id !== 'nodes-container' && 
                e.target.id !== 'edges') return;
            
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            initialOffsetX = offsetX;
            initialOffsetY = offsetY;
        }});
        
        canvas.addEventListener('mousemove', (e) => {{
            if (!isDragging) return;
            
            offsetX = initialOffsetX + (e.clientX - startX);
            offsetY = initialOffsetY + (e.clientY - startY);
            render();
        }});
        
        canvas.addEventListener('mouseup', () => {{
            isDragging = false;
        }});
        
        canvas.addEventListener('mouseleave', () => {{
            isDragging = false;
        }});
        
        canvas.addEventListener('wheel', (e) => {{
            e.preventDefault();
            
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            const zoomFactor = 1.1;
            const newScale = e.deltaY < 0 ? scale * zoomFactor : scale / zoomFactor;
            
            // Zoom toward mouse position
            offsetX = mouseX - (mouseX - offsetX) * (newScale / scale);
            offsetY = mouseY - (mouseY - offsetY) * (newScale / scale);
            
            scale = Math.max(0.1, Math.min(3, newScale));
            render();
        }});
        
        // Initialize
        calculateLayout();
        render();
        
        window.addEventListener('resize', () => {{
            calculateLayout();
            render();
        }});
    </script>
</body>
</html>"""
        
        return html