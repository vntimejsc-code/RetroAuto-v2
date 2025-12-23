# Changelog

All notable changes to RetroAuto v2.

## [2.0.2] - 2025-12-23

### Added
- Feature: Comprehensive Code Quality System v2.0.1
- Encyclopedia v6.0 - Added Under the Hood, Capstone Project, Advanced Debug
- Added llms.txt and full_user_guide.md for AI Context
- [20251223_124018] Implemented IDE Structure Overlay
- [20251223_123022] Implemented IDE Minimap
- [20251223_121605] Audit Complete & Added Navigator Plan

### Changed
- Auto-commit mode, remove Bandit security check
- UI: Hotkey Trigger selector in Interrupts Panel
- [20251223_132005] Finalized Navigator Package & Crash Fixes
- [20251223] Production Hardening: safe_execute wrapper, execution logging, asset validation, OCR check
- [20251223] Complete Visual Editor: add Export/Import Actions  Graph conversion
- [20251223] Visual Editor: add drag-to-connect wiring for connections
- [20251223] Add Visual Flow Editor MVP: NodeItem, SocketItem, FlowScene with pan/zoom
- [20251223] Performance: debounced refresh + incremental update for ActionsPanel
- [20251223] Add Smart IntelliSense: autocomplete for DSL functions, keywords, assets
- [20251223] Fix HybridPanel proxy methods for MainWindow compatibility
- [20251223] Add HybridActionsPanel: GUI + Code side-by-side view with toggle
- [20251223] Fix IDE-Actions sync: empty goto/label, nested markers, new action types support
- [20251222_235800] Completed Assets UX: F2 Rename, Draggable Menu, Persistence
- [20251222_181200] Complete Phase 1/2: Search bar + Double-click edit
- [20251222_181100] Complete Undo/Redo (Ctrl+Z/Y) + Space to Test step
- [20251222_180400] Advanced Visual: Custom delegate with tree lines + expand indicators

### Fixed
- Mypy config and critical type/undefined errors
- Add type annotation for HotkeyListener._initialized
- [20251223_132740] Fixed RecursionError: Merged resizeEvent & unified viewport margins
- [20251223_132343] Fixed duplicate Minimap instantiation crash
- [20251223_130821] Fixed IDE Highlighting & Structure Panel Init
- [20251222_201700] Fix: ClickUntil detail display + Apply handlers in Properties panel
- [20251222_201700] Fix: ClickUntil detail display + Apply handlers in Properties panel
