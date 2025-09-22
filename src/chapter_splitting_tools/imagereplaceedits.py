import os
import re
import wx

def extract_img_tags(html):
    return list(re.finditer(r'<img[^>]+>', html, flags=re.IGNORECASE))

def replace_imgs_by_position(original_html, new_html):
    original_matches = extract_img_tags(original_html)
    new_matches = extract_img_tags(new_html)

    min_count = min(len(original_matches), len(new_matches))
    if min_count == 0:
        return original_html  # No replacements to make

    result = []
    last_index = 0

    for i in range(min_count):
        orig = original_matches[i]
        start, end = orig.span()
        result.append(original_html[last_index:start])
        result.append(new_matches[i].group(0))
        last_index = end

    # Add the remaining part of original HTML
    result.append(original_html[last_index:])
    return ''.join(result)

def main():
    app = wx.App()

    # Select Original HTML
    with wx.FileDialog(None, "Select Original HTML file (to modify)",
                      wildcard="HTML Files (*.html)|*.html|All Files (*.*)|*.*") as dialog:
        if dialog.ShowModal() != wx.ID_OK:
            wx.MessageBox("No HTML file selected.", "Cancelled", wx.OK | wx.ICON_INFORMATION)
            return
        original_path = dialog.GetPath()

    # Select New HTML with replacement <img> tags
    with wx.FileDialog(None, "Select HTML/Text file with new <img> tags (same structure)",
                      wildcard="HTML Files (*.html)|*.html|Text Files (*.txt)|*.txt|All Files (*.*)|*.*") as dialog:
        if dialog.ShowModal() != wx.ID_OK:
            wx.MessageBox("No second HTML/text file selected.", "Cancelled", wx.OK | wx.ICON_INFORMATION)
            return
        new_path = dialog.GetPath()

    with open(original_path, "r", encoding="utf-8") as f:
        original_html = f.read()

    with open(new_path, "r", encoding="utf-8") as f:
        new_html = f.read()

    # Do the replacements
    updated_html = replace_imgs_by_position(original_html, new_html)

    output_path = os.path.join(os.path.dirname(original_path), "output_replaced.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(updated_html)

    wx.MessageBox(f"<img> tags replaced by position.\nSaved as: {output_path}", "Done", wx.OK | wx.ICON_INFORMATION)

if __name__ == "__main__":
    main()
