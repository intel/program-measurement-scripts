-- Print function and loop info for each loop
-- Usage: maqao list_loops.lua <executable_name> <regexp-filter>
-- Output: CSV (function_name,function_demname,orig_function_name,orig_function_demname,loop_ID,loop_depth)
-- About regexp-filter:
--  - to exact match 'foo', use ^foo$
--  - a function is selected if its (mangled) name matches the regexp
--    or if the *demangled* name of its "original function" matches

local asmfile

local binary_name = arg[2]
local proj = project.new ("list_loops")
if string.find (string.lower (binary_name), "%.s$") ~= nil then
   -- TODO: handle properly args.arch in MAQAO core
   asmfile = proj:load_txtfile (binary_name, "x86_64", proj:get_uarch_name());
else
   asmfile = proj:load (binary_name, proj:get_uarch_name());
end
if (asmfile == nil) then
   Message:error ("Cannot analyze "..binary_name);
   os.exit (1);
end

-- Open CSV file
local CSV_file_name = asmfile:get_name() .. ".csv"
local fp = io.open (CSV_file_name, "w")
if fp == nil then
   print ("Cannot open "..CSV_file_name.. " in write-only mode")
else
   print ("Dumping to "..CSV_file_name);
end

-- Print CSV header
fp:write ("function_name,function_demname,orig_function_name,orig_function_demname,")
fp:write ("loop_ID,loop_depth\n")

local config = { fct = arg[3] } -- make happy analyze:fct_matches
for fct in asmfile:functions() do

   -- print the list of loops
   if analyze:fct_matches (config, fct) then
      local name    = fct:get_name   () or ""
      local demname = fct:get_demname() or ""

      local orig_fct = fct:get_original_function()
      local orig_name    = ""
      local orig_demname = ""
      if orig_fct ~= nil then
         orig_name    = orig_fct:get_name   () or ""
         orig_demname = orig_fct:get_demname() or ""
      end

      for loop in fct:innermost_loops() do
         fp:write (string.format ("%s,%s,%s,%s,%d,%s\n",
                                  name, demname, orig_name, orig_demname,
                                  loop:get_id(), loop:get_depth()))
      end
   end
end

fp:close()
