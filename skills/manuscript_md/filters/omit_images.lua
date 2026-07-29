-- Omit embedded images from pandoc output (submission Word files).
-- Captions such as "**Figure 1.** ..." are ordinary paragraphs and are kept.
-- Usage: pandoc ... --lua-filter=script/filters/omit_images.lua

local function is_whitespace_only(inlines)
  for _, el in ipairs(inlines) do
    if el.t == "Space" or el.t == "SoftBreak" or el.t == "LineBreak" then
      -- keep scanning
    elseif el.t == "Str" and el.text:match("^%s*$") then
      -- keep scanning
    else
      return false
    end
  end
  return true
end

local function strip_images(inlines)
  local out = pandoc.List()
  for _, el in ipairs(inlines) do
    if el.t ~= "Image" then
      out:insert(el)
    end
  end
  return out
end

function Para(el)
  el.content = strip_images(el.content)
  if #el.content == 0 or is_whitespace_only(el.content) then
    return {}
  end
  return el
end

function Plain(el)
  el.content = strip_images(el.content)
  if #el.content == 0 or is_whitespace_only(el.content) then
    return {}
  end
  return el
end

function Image(_)
  return {}
end
