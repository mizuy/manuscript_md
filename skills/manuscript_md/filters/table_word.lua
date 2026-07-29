-- Improve pandoc pipe tables for Word (docx):
-- 1. Convert <br> in cells to LineBreak (Table 1 column headers).
-- 2. Replace break-prone spaces in table cells (e.g. "2.0 (0.5–10.0)").
-- 3. Assign wider columns to label and trailing fields on wide tables.
-- Spacing / alignment: patch_docx_tables.py (see TABLE_WORD.md).

local NBSP = utf8.char(0x00A0)
local IDSP = utf8.char(0x3000)

local function leading_halfwidth_to_fullwidth(text)
  local spaces, rest = text:match("^( +)(.*)$")
  if spaces then
    return string.rep(IDSP, #spaces) .. rest
  end
  return text
end

local function protect_str(text)
  text = leading_halfwidth_to_fullwidth(text)
  text = text:gsub(" per (%d+)", " per" .. NBSP .. "%1")
  text = text:gsub(" %(count/exam%)", NBSP .. "(count/exam)")
  return text
end

local function ends_break_prone(text)
  return text:match("[%d%%%-%.]$") ~= nil
end

local function starts_break_prone(text)
  return text:match("^[%(%[]") ~= nil
end

local function protect_inlines(inlines)
  local out = pandoc.List()
  for i, el in ipairs(inlines) do
    if el.t == "RawInline" and el.format:match("html") and el.text:match("^<br%s*/?>$") then
      out:insert(pandoc.LineBreak())
    elseif el.t == "Str" then
      out:insert(pandoc.Str(protect_str(el.text)))
    elseif el.t == "Space" then
      local prev = out[#out]
      local next_el = inlines[i + 1]
      if prev and next_el and prev.t == "Str" and next_el.t == "Str" then
        if ends_break_prone(prev.text) and starts_break_prone(next_el.text) then
          out:insert(pandoc.Str(NBSP))
        else
          out:insert(el)
        end
      else
        out:insert(el)
      end
    elseif el.content then
      el.content = protect_inlines(el.content)
      out:insert(el)
    else
      out:insert(el)
    end
  end
  return out
end

local function process_blocks(blocks)
  for i, block in ipairs(blocks) do
    if block.t == "Plain" or block.t == "Para" then
      block.content = protect_inlines(block.content)
      blocks[i] = block
    end
  end
  return blocks
end

local function process_cell(cell)
  cell.content = process_blocks(cell.content)
  return cell
end

local function process_row(row)
  for i, cell in ipairs(row.cells) do
    row.cells[i] = process_cell(cell)
  end
  return row
end

local function column_weights(n)
  if n <= 4 then
    return { 1.45, 1.0, 1.0, 1.0 }
  end
  local weights = {}
  for i = 1, n do
    weights[i] = 1.0
  end
  weights[1] = 1.25
  weights[n] = 2.1
  if n >= 7 then
    weights[3] = 1.15
    if n >= 8 then
      weights[5] = 1.15
    end
  end
  return weights
end

local function apply_col_widths(colspecs)
  local n = #colspecs
  local weights = column_weights(n)
  local total = 0
  for _, w in ipairs(weights) do
    total = total + w
  end
  for i, spec in ipairs(colspecs) do
    colspecs[i] = { spec[1], weights[i] / total }
  end
  return colspecs
end

function Table(tbl)
  if #tbl.colspecs >= 4 then
    tbl.colspecs = apply_col_widths(tbl.colspecs)
  end

  for _, row in ipairs(tbl.head.rows) do
    process_row(row)
  end
  for _, body in ipairs(tbl.bodies) do
    for _, row in ipairs(body.body) do
      process_row(row)
    end
  end
  if tbl.foot and tbl.foot.rows then
    for _, row in ipairs(tbl.foot.rows) do
      process_row(row)
    end
  end
  return tbl
end
