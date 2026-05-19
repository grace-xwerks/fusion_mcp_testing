import adsk.core

def run(_context: str):
    app = adsk.core.Application.get()
    target = 'fusion_mcp_library_demo_cam_full'
    for i in range(app.documents.count):
        d = app.documents.item(i)
        if d.name == target:
            d.activate()
            print(f"Activated: {d.name}")
            ui = app.userInterface
            ws = ui.workspaces.itemById('CAMEnvironment')
            if ws and ui.activeWorkspace.id != 'CAMEnvironment':
                ws.activate()
            print(f"Workspace: {ui.activeWorkspace.id}")
            return
    print(f"Document {target!r} not found among {app.documents.count} open docs.")
