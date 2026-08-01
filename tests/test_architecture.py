from __future__ import annotations

import ast
import unittest
from collections import defaultdict
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[1] / "src" / "chat_archive_explorer"
PROJECT_PREFIX = "chat_archive_explorer"


def _module_name(path: Path) -> str:
    relative = path.relative_to(PACKAGE_ROOT.parent).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _project_imports(path: Path) -> set[str]:
    imports: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(
                alias.name for alias in node.names if alias.name.startswith(PROJECT_PREFIX)
            )
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith(PROJECT_PREFIX)
        ):
            imports.add(node.module)
    return imports


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_production_modules_have_no_circular_imports(self) -> None:
        module_paths = {_module_name(path): path for path in PACKAGE_ROOT.rglob("*.py")}
        edges: dict[str, set[str]] = defaultdict(set)
        for module, path in module_paths.items():
            for imported in _project_imports(path):
                candidate = imported
                while candidate not in module_paths and "." in candidate:
                    candidate = candidate.rsplit(".", 1)[0]
                if candidate in module_paths and candidate != module:
                    edges[module].add(candidate)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(module: str, trail: tuple[str, ...]) -> None:
            if module in visiting:
                cycle = " -> ".join((*trail, module))
                self.fail(f"Circular import detected: {cycle}")
            if module in visited:
                return
            visiting.add(module)
            for dependency in sorted(edges[module]):
                visit(dependency, (*trail, module))
            visiting.remove(module)
            visited.add(module)

        for module in sorted(module_paths):
            visit(module, ())

    def test_domain_layer_has_no_outward_project_dependencies(self) -> None:
        for path in (PACKAGE_ROOT / "domain").rglob("*.py"):
            for imported in _project_imports(path):
                self.assertTrue(
                    imported == "chat_archive_explorer.domain"
                    or imported.startswith("chat_archive_explorer.domain."),
                    f"Domain layer imports outward dependency {imported} in {path}",
                )

    def test_application_layer_does_not_import_infrastructure_or_presentation(self) -> None:
        forbidden_roots = {
            "blobs",
            "cli",
            "exporters",
            "filesystem",
            "importers",
            "logging_config",
            "presentation",
            "search",
            "storage",
        }
        for path in (PACKAGE_ROOT / "application").rglob("*.py"):
            for imported in _project_imports(path):
                parts = imported.split(".")
                imported_root = parts[1] if len(parts) > 1 else ""
                self.assertNotIn(
                    imported_root,
                    forbidden_roots,
                    f"Application layer imports {imported} in {path}",
                )

    def test_production_code_has_no_unresolved_placeholders(self) -> None:
        forbidden = ("TO" + "DO", "FIX" + "ME", "NotImplemented" + "Error")
        for path in PACKAGE_ROOT.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            for marker in forbidden:
                self.assertNotIn(marker, source, f"Found {marker} in {path}")

            tree = ast.parse(source, filename=str(path))
            pass_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Pass)]
            self.assertEqual(pass_nodes, [], f"Found pass statement in {path}")


if __name__ == "__main__":
    unittest.main()
