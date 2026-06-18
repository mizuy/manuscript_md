-- Convert inline HTML <sup>...</sup> to pandoc Superscript for docx output.
-- Pandoc's markdown reader emits <sup> and </sup> as separate RawInline nodes
-- with plain Str content between them; Word does not superscript that pattern.

local function is_sup_open(el)
  return el.t == "RawInline" and el.format == "html" and el.text == "<sup>"
end

local function is_sup_close(el)
  return el.t == "RawInline" and el.format == "html" and el.text == "</sup>"
end

local function merge_superscripts(inlines)
  local out = {}
  local i = 1
  while i <= #inlines do
    local el = inlines[i]
    if is_sup_open(el) then
      local content = {}
      local j = i + 1
      local closed = false
      while j <= #inlines do
        local inner = inlines[j]
        if is_sup_close(inner) then
          table.insert(out, pandoc.Superscript(content))
          i = j + 1
          closed = true
          break
        end
        table.insert(content, inner)
        j = j + 1
      end
      if not closed then
        table.insert(out, el)
        i = i + 1
      end
    else
      table.insert(out, el)
      i = i + 1
    end
  end
  return out
end

function Inlines(inlines)
  return merge_superscripts(inlines)
end
