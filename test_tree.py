from textual.app import App, ComposeResult
from textual.widgets import Tree

class Demo(App):
    BINDINGS = [("q", "quit", "Quit")]  # press q to quit

    def compose(self) -> ComposeResult:
        tree = Tree("project")
        tree.root.expand()
        src = tree.root.add("src").expand()
        core = src.add("core").expand()
        core.add_leaf("util.py").expand()
        src.add_leaf("app.py").expand()
        tree.root.add_leaf("README.md").expand()
        yield tree

    
def test_tree():
    Demo().run()
