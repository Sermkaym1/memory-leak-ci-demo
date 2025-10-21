# 📚 Archive Directory

This directory contains files that are not essential for the main demo but may be useful for reference or development.

## 📁 Structure

```
archive/
├── old-docs/           # Previous documentation versions
│   ├── DEMO_README.md  # Old demo documentation
│   ├── README_DEMO.md  # Alternative demo docs
│   ├── GITHUB_PAGES_SETUP.md  # GitHub Pages setup guide
│   └── SETUP_SUMMARY.md       # Old setup summary
└── unused-scripts/     # Development scripts not needed for demo
    ├── debug_graph.py  # Graph debugging utilities
    ├── test_demo_local.py      # Local testing script
    └── test_improvements.py    # Experimental improvements
```

## 🎯 Purpose

- **old-docs/**: Previous versions of documentation kept for reference
- **unused-scripts/**: Development utilities that aren't part of the main demo flow

## 🚀 Main Demo Files

For the actual demo, use files in the root directory:
- `README.md` - Main project documentation
- `.github/workflows/` - CI/CD pipelines
- `apps/` - Demo applications
- `tests/` - Test suites
- `index.html` - Landing page

## 🔄 Restoration

If you need any archived files:
```bash
# Restore from archive
cp archive/old-docs/filename.md ./
cp archive/unused-scripts/script.py ./
```

---
*Files archived during project cleanup for better demo experience*