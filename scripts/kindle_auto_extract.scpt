-- Kindle Auto Extract AppleScript
-- Extracts text from the currently open book in Kindle for Mac

tell application "Kindle"
    activate
    delay 1
end tell

tell application "System Events"
    tell process "Kindle"
        -- Select all text
        keystroke "a" using command down
        delay 0.5

        -- Copy
        keystroke "c" using command down
        delay 0.5
    end tell
end tell

-- Get clipboard content
set bookText to the clipboard

-- Return word count for verification
set wordCount to count words of bookText
return "Copied " & wordCount & " words to clipboard"
