# Kindle Book Extraction Guide

This guide explains how to extract text from your Kindle books for use in the Council of Elders knowledge base.

## Method: Calibre + DeDRM Plugin

This is the most efficient method for processing multiple books.

### Step 1: Install Calibre

Download and install Calibre from: https://calibre-ebook.com/download

### Step 2: Install DeDRM Plugin

1. Download the DeDRM plugin from: https://github.com/noDRM/DeDRM_tools/releases
   - Download `DeDRM_tools_X.X.X.zip`

2. Open Calibre

3. Go to **Preferences** → **Plugins** → **Load plugin from file**

4. Select the downloaded ZIP file (you don't need to unzip it)

5. Restart Calibre when prompted

### Step 3: Configure Kindle Serial Number (if needed)

If your books require a serial number:

1. In Calibre: **Preferences** → **Plugins** → **DeDRM** → **Customize plugin**

2. Click "Kindle for Mac/PC" and add your serial number

To find your Kindle serial number:
- Open Kindle app
- Go to **Kindle** → **Settings** → **Device Info**
- Or check: `~/Library/Containers/com.amazon.Lassen/Data/Library/Preferences/`

### Step 4: Import Your Kindle Books

1. Locate your Kindle books:
   ```
   ~/Library/Containers/com.amazon.Lassen/Data/Library/eBooks/
   ```

2. Inside each ASIN folder, look for `.azw` or `.azw3` files

3. Drag the book files into Calibre's main window
   - DeDRM will automatically remove protection during import

### Step 5: Export as ePub

1. Select the imported book(s) in Calibre

2. Right-click → **Convert books** → **Convert individually**

3. Choose **ePub** as the output format

4. Click **OK** to convert

5. Right-click → **Save to disk** → **Save only ePub format to disk**

6. Choose an output folder, recommended:
   ```
   ~/council-of-elders/data/kindle_exports/
   ```

### Step 6: Ingest into Council

Run the ingestion pipeline:

```bash
# Preview what will be ingested
python -m council.knowledge.kindle ~/council-of-elders/data/kindle_exports/ --dry-run

# Actually ingest
python -m council.knowledge.kindle ~/council-of-elders/data/kindle_exports/
```

## Your Kindle Books

Based on your library, these Council-relevant books were found:

| ASIN | Title | Elder |
|------|-------|-------|
| B0041KLCH0 | The 48 Laws of Power | Robert Greene |
| B000W94FE6 | The Art of Seduction | Robert Greene |
| B000W9149K | The 33 Strategies of War | Robert Greene |
| B005MJFA2W | Mastery | Robert Greene |
| B00555X8OA | The 50th Law | Robert Greene |
| B07D23CFGR | 12 Rules for Life | Jordan Peterson |

## Quick Reference: ASIN Folder Locations

```
~/Library/Containers/com.amazon.Lassen/Data/Library/eBooks/B0041KLCH0/  # 48 Laws
~/Library/Containers/com.amazon.Lassen/Data/Library/eBooks/B000W94FE6/  # Art of Seduction
~/Library/Containers/com.amazon.Lassen/Data/Library/eBooks/B000W9149K/  # 33 Strategies
~/Library/Containers/com.amazon.Lassen/Data/Library/eBooks/B005MJFA2W/  # Mastery
~/Library/Containers/com.amazon.Lassen/Data/Library/eBooks/B00555X8OA/  # 50th Law
~/Library/Containers/com.amazon.Lassen/Data/Library/eBooks/B07D23CFGR/  # 12 Rules
```

## Troubleshooting

### "DeDRM failed" Error
- Ensure the plugin is properly installed
- Check that your Kindle serial number is configured
- Try re-downloading the book in the Kindle app

### Book Not Recognized by Ingestion Pipeline
Use explicit flags:
```bash
python -m council.knowledge.kindle mybook.epub --elder greene --title "The 48 Laws of Power"
```

### List All Known Book Mappings
```bash
python -m council.knowledge.kindle --list-mappings
```

## Alternative: Manual Copy-Paste

If Calibre doesn't work, you can manually copy text:

1. Open the book in Kindle app
2. Select text (Cmd+A for all, or select chapters)
3. Copy (Cmd+C)
4. Paste into a `.txt` file
5. Save to `~/council-of-elders/data/kindle_exports/`
6. Run the ingestion pipeline

This is tedious but works for any book.
