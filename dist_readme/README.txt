GITHUB APP INSTALLER v4.5
===========================
Save tokens and money when working with Claude Code.

QUICK START
-----------
1. Double-click "GitHubAppInstaller.exe" to launch
2. Click Browse, pick your code project folder, click Load
3. Click "Bootstrap" (one-time setup, generates context files)
4. Go to "Context Builder" tab
5. Type what you want Claude to do (plain English, typos OK)
6. Code appears automatically. Click "Copy Complete Prompt"
7. Paste into Claude Code. Done!

WHAT IT DOES
------------
Instead of Claude reading your entire codebase every time you ask
a question (thousands of tokens), this tool:

  - Pre-generates project context files Claude reads automatically
  - When you type a request, finds ONLY the relevant code snippets
  - Builds a structured prompt with your request + the right code
  - You paste ONE thing into Claude and it has everything it needs

TYPICAL SAVINGS: 87-95% fewer input tokens per query.

FEATURES
--------
  Dashboard       - Load project, scan, bootstrap, track token savings
  Context Builder - Type what you need, code auto-found, one-click copy
  Quick Grab      - Click a domain (Browser, AI Chat, Files, etc.)
                    to instantly grab all code from that area
  Snippets        - Browse all code organized by domain with search
  Memory          - View persistent context files
  Settings        - Ollama model manager, generation controls, tutorial

REQUIREMENTS
------------
  - Windows 10/11
  - Python NOT required (this is a standalone .exe)
  - Optional: Ollama (localhost:11434) for AI-assisted search
    Download from https://ollama.com if you want smarter search

OLLAMA SETUP (optional, makes search smarter)
----------------------------------------------
1. Download and install Ollama from https://ollama.com
2. Open GitHub App Installer, go to Settings
3. Click one of the model download buttons (qwen2.5:0.5b is smallest)
4. Wait for download, then the tool auto-selects it

WITHOUT Ollama: fuzzy search still works (80%+ accuracy on typos)
WITH Ollama: search can interpret vague requests even better

FILES GENERATED
---------------
When you Bootstrap a project, the tool creates:

  CLAUDE.md          - At your project root (Claude reads this automatically)
  .claude/memory/    - 5 memory files (persistent across sessions)
  .claude/snippets/  - Reusable code organized by category

These files are what save you tokens. Claude loads them instead
of scanning your source code.

TIPS
----
  - Use Quick Grab buttons to grab code by area (non-coders: start here!)
  - The search handles typos: "fix cdp timout" still works
  - Token counter on Dashboard shows how much you've saved
  - Run "Prep (Update)" after changing your code to refresh context
  - The tool auto-scans every 10 minutes for file changes

TROUBLESHOOTING
---------------
  "No snippets found"  -> Click Bootstrap on Dashboard first
  "Load a project"     -> Browse and Load a folder on Dashboard
  Search finds nothing -> Try different words, or use Quick Grab
  GUI won't launch     -> Make sure Windows Defender isn't blocking it
                          (right-click exe -> Properties -> Unblock)

LICENSE: MIT
VERSION: 4.5.0
