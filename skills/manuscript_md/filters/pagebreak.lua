-- Insert a Word page break for ::: pagebreak fenced divs.
-- Usage in markdown:
--   ::: pagebreak
--   :::

local openxml_pagebreak =
  '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'

function Div(el)
  if el.classes:includes('pagebreak') then
    return pandoc.RawBlock('openxml', openxml_pagebreak)
  end
end
