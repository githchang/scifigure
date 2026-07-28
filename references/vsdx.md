# VSDX export

SciFigure writes a standards-based Open Packaging Conventions ZIP package containing Visio XML parts. Every group, node, annotation, and connector path is written as a separate editable vector shape. Text remains text. The PNG is not embedded as the entire page.

The exporter intentionally avoids shape protection. Users can move, delete, recolor, resize, and edit text in Visio. Connector paths are editable vector line shapes and include semantic connection records. They are not guaranteed to auto-reroute like every Visio desktop dynamic-connector master after arbitrary manual movement.

The structural validator checks package parts and XML parseability. Where LibreOffice is installed, it can also be used as a secondary import smoke test, but Microsoft Visio remains the authoritative application for final manual inspection.
