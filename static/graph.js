// static/graph.js
(function (w) {
  // --- helpers (unchanged) ---
  function truncateLabel(s, n) {
    if (!s) return s;
    return s.length <= n ? s : s.slice(0, n - 1) + "…";
  }
  function wrapByWords(text, maxPerLine) {
    if (!text) return "";
    const words = String(text).split(/\s+/);
    let line = "", out = [];
    for (const w of words) {
      if ((line + " " + w).trim().length > maxPerLine) {
        out.push(line.trim());
        line = w;
      } else {
        line += " " + w;
      }
    }
    if (line.trim()) out.push(line.trim());
    return out.join("\n"); // vis-network uses \n
  }

  function ensureVis(cb) {
    if (w.vis) return cb();
    const s = document.createElement('script');
    s.src = 'https://unpkg.com/vis-network/standalone/umd/vis-network.min.js';
    s.onload = cb;
    document.head.appendChild(s);
  }

  function prepNodes(rawNodes) {
    return rawNodes.map(n => {
      const titleOnly   = String(n.id);
      const statsLine   = (n.label || "").split("\n").slice(1).join("\n");
      const wrappedFull = wrapByWords(titleOnly, 32);
      const shortTitle  = truncateLabel(titleOnly, 48);
      const shortLabel  = shortTitle + (statsLine ? "\n" + statsLine : "");
      const longLabel   = wrappedFull + (statsLine ? "\n" + statsLine : "");
      return {
        id: n.id,
        label: shortLabel,
        title: titleOnly,
        _shortLabel: shortLabel,
        _longLabel: longLabel,
        _isShort: true,
        shape: "circle",
        color: n.color || { background: '#27AE60', border: '#66BB6A' },
      };
    });
  }

  function buildOptions() {
    return {
      physics: {
        enabled: true,
        stabilization: false,
        solver: 'repulsion',
        repulsion: {
          nodeDistance: 1500,
          springLength: 300,
          springConstant: 0.03,
          damping: 0.09,
          centralGravity: 0.0,
        },
      },
      interaction: { hover: true, dragNodes: true, zoomView: true, zoomSpeed: 0.6, navigationButtons: true, dragView: true },
      edges: { width: 15 },
      nodes: {
        shape: "circle",
        shadow: { enabled: true, size: 15, x: 7, y: 7 },
        margin: 120,
        size: 80,
        widthConstraint: { maximum: 180 },
        font: { size: 12 },
      },
    };
  }

  function init(selector, rawNodes, rawEdges) {
    ensureVis(() => {
      const container = document.querySelector(selector);
      const nodesDS = new vis.DataSet(prepNodes(rawNodes || []));
      const edgesDS = new vis.DataSet(rawEdges || []);
      const network = new vis.Network(container, { nodes: nodesDS, edges: edgesDS }, buildOptions());

      network.on("doubleClick", params => {
        if (!params.nodes || !params.nodes.length) return;
        const id = params.nodes[0];
        const n = nodesDS.get(id);
        if (!n) return;
        const next = n._isShort ? n._longLabel : n._shortLabel;
        nodesDS.update({ id, label: next, _isShort: !n._isShort });
      });

      // optional debug API
      w.Graph = { network, nodes: nodesDS, edges: edgesDS };
    });
  }

  // expose a callable
  w.GraphWidget = { init };
})(window);
