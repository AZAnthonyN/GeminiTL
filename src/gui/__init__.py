# gui/__init__.py
"""
GUI entrypoint for the Gemini novel translation tool.
"""

from .app import TranslationApp
import wx

def main():
    app = wx.App()
    frame = TranslationApp()
    frame.Show()
    app.MainLoop()

if __name__ == "__main__":
    main()
