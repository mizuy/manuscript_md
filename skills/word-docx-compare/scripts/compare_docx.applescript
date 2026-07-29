on run argv
	if (count of argv) < 2 then
		error "Usage: compare_docx.applescript BASE.docx CHANGED.docx [OUTPUT.docx] [DETECT_FORMAT]" number 2
	end if

	set basePath to item 1 of argv as text
	set changedPath to item 2 of argv as text
	set baseDoc to POSIX file basePath
	set changedDoc to POSIX file changedPath

	set outPath to ""
	if (count of argv) >= 3 then
		set outPath to item 3 of argv as text
	end if

	set detectFormat to false
	if (count of argv) >= 4 then
		set detectFormatArg to item 4 of argv as text
		if detectFormatArg is "true" or detectFormatArg is "1" or detectFormatArg is "yes" then
			set detectFormat to true
		end if
	end if

	tell application "Microsoft Word"
		activate
		-- Open changed doc once so Word can access it (sandbox workaround).
		open changedDoc
		close active document saving no
		open baseDoc
		if detectFormat then
			compare active document path changedDoc detect format changes true
		else
			compare active document path changedDoc detect format changes false
		end if
		if outPath is not "" and outPath is not "-" then
			set newDoc to active document
			save as newDoc file name (POSIX file outPath)
			close newDoc saving no
			try
				close every document saving no
			end try
			quit saving no
		end if
	end tell
end run
