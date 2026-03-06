#!/usr/bin/env python3.14

import iterm2
import aiohttp
from aiohttp import web
import socket
import json
import os

# Ayarları ve Sunucuları Kaydedeceğimiz JSON Dosyasının Yolu
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "snippets.json")

# NATIVE ITERM2 LOOK & FEEL + LUCIDE SVGS + INDENTATION
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        :root {
            --bg-color: #353535; /* iTerm Native Gray */
            --header-bg: #353535;
            --list-bg: #1a1a1a; /* Inset List Black */
            --border-color: #444;
            --text-color: #ccc;
            --text-dim: #888;
            --hover-bg: #444;
            --accent-color: #004DC5; /* Requested Navy Blue */
            --font-size: 11px;
            --row-height: 20px;
            --icon-stroke: #004DC5;
        }

        * {
            user-select: none;
            -webkit-user-select: none;
        }

        input, textarea {
            user-select: text;
            -webkit-user-select: text;
        }

        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; 
            margin: 0; padding: 0; background-color: var(--bg-color); color: var(--text-color); 
            font-size: var(--font-size); overflow: hidden; height: 100vh; display: flex; flex-direction: column;
        }

        /* SVG Icon Base Styling */
        .icon-svg { width: 12px; height: 12px; stroke: currentColor; stroke-width: 2; fill: none; vertical-align: middle; }
        .icon-small { width: 10px; height: 10px; }

        /* Search Header */
        .search-container {
            padding: 6px 8px; background: var(--header-bg); border-bottom: 1px solid #222;
            display: flex; align-items: center; position: relative;
        }
        .search-box {
            flex: 1; background: #000; border: 1px solid #444; color: white;
            padding: 2px 8px 2px 26px; border-radius: 4px; font-size: var(--font-size); outline: none;
        }
        .search-box:focus { border-color: #666; }
        .search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: var(--text-dim); pointer-events: none; display: flex; align-items: center; }

        /* Inset List Container */
        #list-wrapper {
            flex: 1; margin: 0 8px 8px 8px; background: var(--list-bg); border: 1px solid #222;
            border-radius: 4px; overflow-y: auto; overflow-x: hidden; position: relative;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
        }
        
        #content { min-height: 100%; }

        .group-header {
            background: #252525; padding: 4px 8px; border-bottom: 1px solid #111;
            font-weight: bold; font-size: 10px; color: var(--text-dim); text-transform: uppercase;
            display: flex; align-items: center; cursor: pointer; user-select: none;
        }
        .group-header:hover { background: #2a2a2a; }
        .group-header .toggle-icon { width: 12px; margin-right: 6px; transition: transform 0.2s; color: var(--icon-stroke); display: flex; align-items: center; justify-content: center; }
        .group-header.collapsed .toggle-icon { transform: rotate(-90deg); }
        .group-name-text { flex: 1; }
        .group-actions { display: none; gap: 6px; margin-left:8px;}
        .group-header:hover .group-actions { display: flex; }
        .group-act-btn { color: var(--text-dim); cursor: pointer; display: flex; align-items: center; }
        .group-act-btn:hover { color: white; }

        .server-item {
            display: flex; align-items: center; padding: 0 8px; height: var(--row-height);
            border-bottom: 1px solid #222; cursor: default; user-select: none;
        }
        .server-item.indented { padding-left: 26px; /* Align with the text of the group header */ }
        .server-item:hover { background: var(--hover-bg); }
        .server-item.selected { background: var(--accent-color); color: white; }
        .server-item.selected .server-icon { color: white; }
        .server-item.dragging { opacity: 0.5; background: #333; }
        
        .server-icon { margin-right: 8px; color: #4a90e2; display: flex; align-items: center; }
        .server-name { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .server-sub { color: var(--text-dim); font-size: 10px; margin-left: 8px; }
        .selected .server-sub { color: #eee; }

        /* Bottom Toolbar */
        .toolbar {
            height: 24px; background: var(--header-bg); border-top: 1px solid #222;
            display: flex; align-items: center; padding: 0 8px; gap: 4px;
        }
        .tool-btn {
            min-width: 20px; height: 20px; display: flex; align-items: center; justify-content: center;
            border-radius: 2px; cursor: pointer; color: var(--text-color); font-size: 14px;
            padding: 0 4px; 
        }
        .tool-btn:hover { background: #555; }
        .tool-btn.disabled { opacity: 0.3; cursor: default; }
        .tool-sep { width: 1px; height: 14px; background: #444; margin: 0 2px; }

        /* Modal */
        #modal { 
            position: fixed; top: 0; left: 0; right: 0; bottom: 0; 
            background: rgba(0,0,0,0.6); z-index: 100; 
            display: none; align-items: center; justify-content: center;
            padding: 16px; 
        }
        .modal-content { 
            background: #353535; border: 1px solid #555; border-radius: 6px; 
            padding: 12px; width: 100%; max-width: 300px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
        }
        .form-row { display: flex; flex-direction: column; margin-bottom: 8px; }
        .form-row label { font-size: 10px; color: var(--text-dim); margin-bottom: 2px; }
        .form-row input, .form-row select { background: #111; border: 1px solid #444; color: white; padding: 4px 6px; border-radius: 3px; font-size: 11px; outline: none; width: 100%; box-sizing: border-box; }
        
        .row-flex { display: flex; gap: 8px; }
        .row-flex > div { flex: 1; }

        .radio-group { display: flex; flex-wrap: wrap; gap: 16px; margin-top: 6px; }
        .radio-item { display: flex; align-items: center; gap: 8px; color: white; font-size: 11px; cursor: pointer; white-space: nowrap; }
        .radio-item input { width: auto; margin: 0; }

        .modal-actions { margin-top: 12px; display: flex; justify-content: flex-end; gap: 6px; border-top: 1px solid #444; padding-top: 10px; }
        .btn { padding: 4px 12px; border-radius: 3px; cursor: pointer; border: 1px solid #555; background: #444; color: white; font-size: 11px; }
        .btn:hover { background: #555; }
        .btn-primary { background: #0b4f96; border-color: #0b4f96; }

        /* Context Menu */
        #ctx-menu {
            display: none; position: fixed; background: #2a2a2a; border: 1px solid #444;
            border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); z-index: 1000;
            padding: 4px 0; min-width: 140px;
        }
        .ctx-item {
            padding: 4px 12px; cursor: pointer; display: flex; align-items: center; gap: 8px;
            font-size: 11px; color: #ccc;
        }
        .ctx-item:hover { background: var(--accent-color); color: white; }
        .ctx-item .icon-svg { opacity: 0.7; }
        .ctx-sep { height: 1px; background: #444; margin: 4px 0; }
    </style>
</head>
<body onclick="deselect(event)" oncontextmenu="return false;">
    <div id="ctx-menu"></div>
    <div class="search-container">
        <span class="search-icon"><svg class="icon-svg icon-small" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></span>
        <input type="text" id="searchInput" class="search-box" placeholder="Search" onkeyup="renderServers()">
    </div>
    
    <div id="list-wrapper">
        <div id="content"></div>
    </div>

    <div class="toolbar">
        <div class="tool-btn" onclick="openModal()" title="Add Host">
            <svg class="icon-svg" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        </div>
        <div class="tool-btn" id="btn-remove" onclick="deleteSelected()" title="Remove Host">
            <svg class="icon-svg" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>
        </div>
        <div class="tool-sep"></div>
        <div class="tool-btn" id="btn-edit-tool" onclick="editSelected()" title="Edit Host">
            <svg class="icon-svg" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
        </div>
        <div class="tool-sep"></div>
        <div class="tool-btn" onclick="addGroup()" title="Add Group">
            <svg class="icon-svg" style="margin-right:2px;" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/><line x1="12" y1="11" x2="12" y2="17"/><line x1="9" y1="14" x2="15" y2="14"/></svg>
        </div>
    </div>

    <!-- Modal -->
    <div id="modal" onclick="closeModalOnOuterClick(event)">
        <div class="modal-content" style="max-width: 400px;" onclick="event.stopPropagation()">
            <input type="hidden" id="edit-id">
            <div id="host-fields">
                <div class="row-flex">
                    <div class="form-row" style="flex:2;"><label>Snippet Name:</label><input type="text" id="inp-name"></div>
                    <div class="form-row" style="flex:1;">
                        <label>Group:</label>
                        <input type="text" id="inp-group" list="group-list" placeholder="None">
                        <datalist id="group-list"></datalist>
                    </div>
                </div>

                <div class="form-row">
                    <label>Command:</label>
                    <textarea id="inp-command" rows="8" style="background:#111; border:1px solid #444; color:white; padding:6px; border-radius:3px; font-size:12px; font-family:monospace; outline:none; resize:vertical;"></textarea>
                </div>
            </div>

            <div id="group-fields" style="display:none;">
                <div class="form-row"><label>Group Name:</label><input type="text" id="inp-group-name"></div>
            </div>

            <div id="confirm-fields" style="display:none; text-align: center; padding: 10px;">
                <p id="confirm-msg" style="font-size: 13px; margin-bottom: 20px; color: white;"></p>
                <div class="row-flex" style="justify-content: center; gap: 15px;">
                    <button class="btn" onclick="closeModal()">Cancel</button>
                    <button class="btn btn-primary" id="btn-confirm-yes" style="background: #c33; border-color: #c33;">Confirm</button>
                </div>
            </div>
            
            <div class="modal-actions" id="modal-actions">
                <button class="btn" onclick="closeModal()">Cancel</button>
                <button class="btn btn-primary" id="btn-save" onclick="saveServer()">Save</button>
            </div>
        </div>
    </div>

    <script>
        const SVGS = {
            chevron: '<svg class="icon-svg icon-small" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>',
            terminal: '<svg class="icon-svg" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>',
            edit: '<svg class="icon-svg icon-small" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
            trash: '<svg class="icon-svg icon-small" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>',
            plus: '<svg class="icon-svg icon-small" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
            refresh: '<svg class="icon-svg icon-small" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0115-6.7L21 8"/><path d="M3 22v-6h6"/><path d="M21 12a9 9 0 01-15 6.7L3 16"/></svg>'
        };

        let servers = [];
        let selectedId = null;
        let collapsedGroups = new Set();
        let modalMode = 'host';

        function hideContextMenu() {
            document.getElementById('ctx-menu').style.display = 'none';
        }

        function showContextMenu(e, type, id) {
            e.preventDefault();
            e.stopPropagation();
            const menu = document.getElementById('ctx-menu');
            const safeId = String(id).replace(/'/g, "\\'");
            
            let items = '';
            if (type === 'snippet') {
                items = `
                    <div class="ctx-item" onclick="connect('${safeId}'); hideContextMenu();">${SVGS.plus} Run Snippet</div>
                    <div class="ctx-item" onclick="connect('${safeId}', 'current'); hideContextMenu();">${SVGS.refresh} Paste Snippet</div>
                    <div class="ctx-sep"></div>
                    <div class="ctx-item" onclick="openModal('${safeId}'); hideContextMenu();">${SVGS.edit} Edit</div>
                    <div class="ctx-item" onclick="deleteServerById('${safeId}'); hideContextMenu();">${SVGS.trash} Delete</div>
                `;
            } else if (type === 'group') {
                items = `
                    <div class="ctx-item" onclick="renameGroup('${safeId}', event); hideContextMenu();">${SVGS.edit} Rename Group</div>
                    <div class="ctx-item" onclick="deleteGroup('${safeId}', event); hideContextMenu();">${SVGS.trash} Delete Group</div>
                `;
            }
            menu.innerHTML = items;
            menu.style.display = 'block';
            
            // Position adjusting to stay within viewport
            let x = e.clientX;
            let y = e.clientY;
            if (x + 150 > window.innerWidth) x -= 140;
            if (y + 150 > window.innerHeight) y -= 100;
            
            menu.style.left = x + 'px';
            menu.style.top = y + 'px';

            const closeMenu = (ev) => {
                if (menu.contains(ev.target)) return;
                hideContextMenu();
                document.removeEventListener('mousedown', closeMenu);
            };
            setTimeout(() => document.addEventListener('mousedown', closeMenu), 50);
        }

        async function loadServers() {
            let res = await fetch('/get_servers');
            servers = await res.json();
            servers.sort((a, b) => (a.order || 0) - (b.order || 0));
            updateGroupList();
            renderServers();
        }

        function updateGroupList() {
            const list = document.getElementById('group-list');
            const groups = [...new Set(servers.map(s => s.group).filter(g => g))];
            list.innerHTML = groups.map(g => `<option value="${g}">`).join('');
        }

        async function moveServer(fromId, toId, intoGroup = null) {
            const fromIdx = servers.findIndex(s => s.id === fromId);
            const item = servers[fromIdx];
            if (!item) return;

            if (intoGroup !== null) {
                item.group = intoGroup === "UNGROUPED" ? "" : intoGroup;
            } else {
                const toSrv = servers.find(s => s.id === toId);
                if (toSrv) item.group = toSrv.group || "";
                const toIdx = servers.findIndex(s => s.id === toId);
                servers.splice(fromIdx, 1);
                servers.splice(toIdx, 0, item);
            }

            servers.forEach((s, i) => s.order = i);
            await fetch('/save_batch', { method: 'POST', body: JSON.stringify(servers) });
            loadServers();
        }

        function renderServers() {
            const container = document.getElementById('content');
            const query = document.getElementById('searchInput').value.toLowerCase();
            container.innerHTML = "";

            const groupedSet = new Set(servers.map(s => s.group || "UNGROUPED"));
            const grouped = {};
            groupedSet.forEach(g => grouped[g] = []);

            servers.forEach(s => {
                if (query && !s.name.toLowerCase().includes(query) && !s.host.toLowerCase().includes(query)) return;
                const g = s.group || "UNGROUPED";
                grouped[g].push(s);
            });

            const sortedGroups = Object.keys(grouped).sort((a,b) => {
                if(a === "UNGROUPED") return 1;
                if(b === "UNGROUPED") return -1;
                return a.localeCompare(b);
            });

            sortedGroups.forEach(groupName => {
                const isCollapsed = collapsedGroups.has(groupName);
                const hasHosts = grouped[groupName].length > 0;
                
                if (!hasHosts && query) return;

                const gDiv = document.createElement('div');
                gDiv.className = `group-header ${isCollapsed ? 'collapsed' : ''}`;
                const safeNameAttr = groupName.replace(/'/g, "\\'");
                gDiv.innerHTML = `
                    <span class="toggle-icon">${SVGS.chevron}</span>
                    <span class="group-name-text">${groupName}</span>
                    <div class="group-actions">
                        ${groupName !== 'UNGROUPED' ? `<span class="group-act-btn" onclick="renameGroup('${safeNameAttr}', event)" title="Rename">${SVGS.edit}</span>` : ''}
                        ${groupName !== 'UNGROUPED' && !hasHosts ? `<span class="group-act-btn" onclick="deleteGroup('${safeNameAttr}', event)" title="Delete">${SVGS.trash}</span>` : ''}
                    </div>
                `;
                
                gDiv.onclick = (e) => {
                    if (isCollapsed) collapsedGroups.delete(groupName);
                    else collapsedGroups.add(groupName);
                    renderServers();
                    e.stopPropagation();
                };
                gDiv.oncontextmenu = (e) => {
                    if (groupName !== 'UNGROUPED') showContextMenu(e, 'group', groupName);
                };

                gDiv.ondragover = (e) => { e.preventDefault(); gDiv.style.background = "#444"; };
                gDiv.ondragleave = () => gDiv.style.background = "";
                gDiv.ondrop = (e) => {
                    e.preventDefault(); gDiv.style.background = "";
                    const draggedId = e.dataTransfer.getData("text/plain");
                    moveServer(draggedId, null, groupName);
                };

                container.appendChild(gDiv);

                if (!isCollapsed) {
                    grouped[groupName].forEach(srv => {
                        if (srv.virtual) return; 
                        const sDiv = document.createElement('div');
                        const isIndented = groupName !== 'UNGROUPED';
                        sDiv.className = `server-item ${selectedId === srv.id ? 'selected' : ''} ${isIndented ? 'indented' : ''}`;
                        sDiv.draggable = true;
                        sDiv.innerHTML = `
                            <span class="server-icon">${SVGS.terminal}</span>
                            <span class="server-name">${srv.name}</span>
                        `;
                        
                        sDiv.onclick = (e) => {
                            selectedId = srv.id;
                            updateToolbar();
                            renderServers();
                            e.stopPropagation();
                        };
                        sDiv.oncontextmenu = (e) => {
                            selectedId = srv.id;
                            updateToolbar();
                            document.querySelectorAll('.server-item').forEach(el => el.classList.remove('selected'));
                            sDiv.classList.add('selected');
                            showContextMenu(e, 'snippet', srv.id);
                        };
                        sDiv.ondblclick = () => connect(srv.id);
                        sDiv.ondragstart = (e) => {
                            e.dataTransfer.setData("text/plain", srv.id);
                            sDiv.classList.add('dragging');
                        };
                        sDiv.ondragend = () => sDiv.classList.remove('dragging');
                        sDiv.ondragover = (e) => { e.preventDefault(); sDiv.style.borderTop = "2px solid #0b4f96"; };
                        sDiv.ondragleave = () => sDiv.style.borderTop = "";
                        sDiv.ondrop = (e) => {
                            e.preventDefault(); sDiv.style.borderTop = "";
                            const draggedId = e.dataTransfer.getData("text/plain");
                            moveServer(draggedId, srv.id);
                        };
                        container.appendChild(sDiv);
                    });
                }
            });
            updateToolbar();
        }

        function updateToolbar() {
            const hasSel = !!selectedId;
            document.getElementById('btn-remove').classList.toggle('disabled', !hasSel);
            document.getElementById('btn-edit-tool').classList.toggle('disabled', !hasSel);
        }

        function deselect(e) { 
            if (e.target.closest('.server-item') || e.target.closest('.toolbar') || e.target.closest('#modal') || e.target.closest('.group-act-btn')) return;
            selectedId = null; updateToolbar(); renderServers(); 
        }

        function toggleAuth() {
            const isKey = document.querySelector('input[name="auth"]:checked').value === 'key';
            document.getElementById('lbl-pass').innerText = isKey ? 'Key Path:' : 'Password:';
            document.getElementById('inp-pass').type = isKey ? 'text' : 'password';
        }

        function setModalPanel(panel) {
            document.getElementById('host-fields').style.display = panel === 'host' ? 'block' : 'none';
            document.getElementById('group-fields').style.display = panel === 'group' ? 'block' : 'none';
            document.getElementById('confirm-fields').style.display = panel === 'confirm' ? 'block' : 'none';
            document.getElementById('modal-actions').style.display = panel === 'confirm' ? 'none' : 'flex';
            document.getElementById('modal').style.display = 'flex';
        }

        function showConfirm(msg, callback) {
            setModalPanel('confirm');
            document.getElementById('confirm-msg').innerText = msg;
            document.getElementById('btn-confirm-yes').onclick = () => {
                closeModal();
                callback();
            };
        }

        function openModal(id = null) {
            modalMode = 'snippet';
            setModalPanel('host');
            document.getElementById('btn-save').onclick = saveServer;

            const srv = id ? servers.find(s => s.id === id) : null;
            document.getElementById('edit-id').value = id || '';
            document.getElementById('inp-name').value = srv?.name || '';
            document.getElementById('inp-group').value = srv?.group || '';
            document.getElementById('inp-command').value = srv?.command || '';
        }

        function addGroup() {
            modalMode = 'group';
            setModalPanel('group');
            document.getElementById('inp-group-name').value = '';
            document.getElementById('inp-group-name').focus();
            document.getElementById('btn-save').onclick = async () => {
                const name = document.getElementById('inp-group-name').value;
                if (!name) return;
                const data = { id: 'group_' + Date.now(), group: name, virtual: true, name: '', host: '', user: '', password: '', order: servers.length };
                await fetch('/save_server', { method: 'POST', body: JSON.stringify(data) });
                closeModal();
                loadServers();
            };
        }

        function renameGroup(oldName, e) {
            if (e) e.stopPropagation();
            modalMode = 'rename_group';
            setModalPanel('group');
            document.getElementById('inp-group-name').value = oldName;
            document.getElementById('inp-group-name').focus();
            document.getElementById('btn-save').onclick = async () => {
                const newName = document.getElementById('inp-group-name').value;
                if (newName && newName !== oldName) {
                    servers.forEach(s => { if (s.group === oldName) s.group = newName; });
                    await fetch('/save_batch', { method: 'POST', body: JSON.stringify(servers) });
                    loadServers();
                }
                closeModal();
            };
        }

        function deleteGroup(groupName, e) {
            if (e) e.stopPropagation();
            const realServers = servers.filter(s => s.group === groupName && !s.virtual);
            const virtualServers = servers.filter(s => s.group === groupName && s.virtual);

            let msg = `Delete group "${groupName}"?`;
            if (realServers.length > 0) {
                msg = `Group "${groupName}" contains ${realServers.length} servers. They will be moved to UNGROUPED. Continue?`;
            }

            showConfirm(msg, () => {
                // Move real servers to ungrouped
                servers.forEach(s => {
                    if (s.group === groupName && !s.virtual) s.group = "";
                });
                // Remove virtual group entries
                const idsToDelete = virtualServers.map(v => v.id);
                const updatedServers = servers.filter(s => !idsToDelete.includes(s.id));
                
                // Save the entire state accurately
                fetch('/save_batch', { method: 'POST', body: JSON.stringify(updatedServers) }).then(() => loadServers());
            });
        }

        function closeModal() { document.getElementById('modal').style.display = 'none'; }
        function closeModalOnOuterClick(e) { if(e.target === document.getElementById('modal')) closeModal(); }

        async function saveServer() {
            const id = document.getElementById('edit-id').value || Date.now().toString();
            const data = {
                id: id,
                name: document.getElementById('inp-name').value,
                command: document.getElementById('inp-command').value,
                group: document.getElementById('inp-group').value,
                order: servers.find(s => s.id === id)?.order ?? servers.length
            };
            await fetch('/save_server', { method: 'POST', body: JSON.stringify(data) });
            closeModal();
            loadServers();
        }

        async function deleteSelected() {
            if (!selectedId) return;
            deleteServerById(selectedId);
        }

        async function deleteServerById(id) {
            showConfirm('Delete selected host?', () => {
                fetch('/delete_server', { method: 'POST', body: id }).then(() => {
                    if (selectedId === id) selectedId = null;
                    loadServers();
                });
            });
        }

        function editSelected() { if (selectedId) openModal(selectedId); }
        function connect(id, mode = 'new') { fetch('/connect', { method: 'POST', body: JSON.stringify({id, mode}) }); }

        document.addEventListener('keydown', function(e) {
            if (document.getElementById('modal').style.display === 'flex') {
                if (e.key === 'Escape') {
                    closeModal();
                } else if (e.key === 'Enter') {
                    if (e.target.tagName.toLowerCase() === 'textarea' && !e.ctrlKey && !e.metaKey) return;
                    e.preventDefault();
                    if (document.getElementById('confirm-fields').style.display === 'block') {
                        document.getElementById('btn-confirm-yes').click();
                    } else if (document.getElementById('modal-actions').style.display !== 'none') {
                        document.getElementById('btn-save').onclick();
                    }
                }
            }
        });

        loadServers();
    </script>
</body>
</html>
"""

def load_db():
    if not os.path.exists(DB_PATH): return []
    with open(DB_PATH, "r", encoding="utf-8") as f: 
        try:
            data = json.load(f)
            return [s for s in data if isinstance(s, dict) and "id" in s]
        except: return []

def save_db(data):
    with open(DB_PATH, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]

async def main(connection):
    app = await iterm2.async_get_app(connection)

    async def handle_index(request): return web.Response(text=HTML_PAGE, content_type='text/html')
    async def handle_get_servers(request): return web.json_response(load_db())
    async def handle_save_server(request):
        data = await request.json()
        servers = load_db()
        existing = next((s for s in servers if s["id"] == data["id"]), None)
        if existing: existing.update(data)
        else: servers.append(data)
        save_db(servers)
        return web.Response(text="OK")

    async def handle_save_batch(request):
        data = await request.json()
        save_db(data)
        return web.Response(text="OK")

    async def handle_delete_server(request):
        server_id = await request.text()
        servers = [s for s in load_db() if s["id"] != server_id]
        save_db(servers)
        return web.Response(text="OK")

    async def handle_connect(request):
        data = await request.json()
        server_id = data.get("id")
        mode = data.get("mode", "new")
        srv = next((s for s in load_db() if s["id"] == server_id), None)
        if not srv or srv.get("virtual"): return web.Response(text="Not Found")
        window = app.current_terminal_window
        if window:
            session = window.current_tab.current_session
            command = srv.get("command", "")
            if command:
                if mode == "new":
                    await session.async_send_text(command + "\n")
                else:
                    await session.async_send_text(command)

        return web.Response(text="OK")

    web_app = web.Application()
    web_app.add_routes([
        web.get('/', handle_index),
        web.get('/get_servers', handle_get_servers),
        web.post('/save_server', handle_save_server),
        web.post('/save_batch', handle_save_batch),
        web.post('/delete_server', handle_delete_server),
        web.post('/connect', handle_connect)
    ])
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    free_port = get_free_port()
    site = web.TCPSite(runner, 'localhost', free_port)
    await site.start()
    await iterm2.tool.async_register_web_view_tool(connection, "Snippets Manager", "com.benim.snippetmanager", True, f"http://localhost:{free_port}/" )

iterm2.run_forever(main)