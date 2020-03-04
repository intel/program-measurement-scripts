---
--  Copyright (C) 2004 - 2019 UniversitÃ© de Versailles Saint-Quentin-en-Yvelines (UVSQ)
--
-- This file is part of MAQAO.
--
-- MAQAO is free software; you can redistribute it and/or
--  modify it under the terms of the GNU Lesser General Public License
--  as published by the Free Software Foundation; either version 3
--  of the License, or (at your option) any later version.
--
--  This program is distributed in the hope that it will be useful,
--  but WITHOUT ANY WARRANTY; without even the implied warranty of
--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
--  GNU Lesser General Public License for more details.
--
--  You should have received a copy of the GNU Lesser General Public License
--  along with this program; if not, write to the Free Software
--  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
---

local function get_destination_register (insn)
   local operands = insn:get_registers_rw();

   if (operands == nil) then return end

   -- for each operand of the current uop/instruction
   for _,op in pairs (operands) do
      -- if written register
      if (op ["write"] == true) then return op ["value"] end
   end
end

local function modifies_register (insn, reg)
   local operands = insn:get_registers_rw();

   if (operands == nil) then return false end

   -- for each operand of the current uop/instruction
   for _,op in pairs (operands) do
      -- if written register
      if (op ["write"] == true) then return (op ["value"] == reg) end
   end

   return false;
end

-- TODO: pasted from get_vec_eff => factorize
-- Compute the used vector size (in bytes)
local function get_used_size (insn)
   local used_size = insn:get_read_bits();
   if (used_size == 0) then used_size = insn:get_element_bits() end
   if (used_size == 0) then
      Debug:warn ("Cannot guess size of elements for ["..insn:get_asm_code().."]")
   end

   return (used_size / 8);
end

local function get_wasted_bytes (insns, rank)
   local target_insn = insns[rank]
   local reg = get_destination_register (target_insn);
   if (reg == nil) then return 0 end

   local src_rank; -- rank of the instruction writing to the ANDPS destination register
   local n = #insns;

   -- for each instruction, in reverse order, starting from the target instruction
   for i = 1, n do
      if (rank > i) then
         if (modifies_register (insns [rank - i], reg)) then
            src_rank = rank - i;
            break;
         end
      else -- loop from the end of the table
         if (modifies_register (insns [n + rank - i], reg)) then
            src_rank = n + rank - i;
            break;
         end
      end
   end

   if (src_rank ~= nil) then
      local mem_oprnd = target_insn:get_first_mem_oprnd ();
      local src_insn_used_size = get_used_size (insns [src_rank]);

      if (src_insn_used_size ~= nil) then
         return (mem_oprnd ["size"] / 8) - src_insn_used_size;
      end
   end

   return 0;
end

------------------------- scalar INT -------------------------

local function lookup_scalar_INT_insns (cqa_results)
   local insns = {}
   local i = 1

   local is_loop_ctrl = cqa.api.mod.is_loop_ctrl
   local cqa_context = cqa_results.common.context

   for _,insn in ipairs (cqa_results.insns) do
      if (insn:is_INT() and not insn:is_SIMD_INT() and
          not is_loop_ctrl (insn, cqa_context.cmp_insn)) then
         insns[i] = insn
         i = i + 1
      end
   end

   return insns
end

local function get_scalar_INT_arith_op (insn)
   if (insn:get_class() ~= Consts.C_ARITH) then return nil end

   local fam = insn:get_family()
   local fam2op = { [Consts.FM_ADD] = "ADD/SUB", [Consts.FM_SUB] = "ADD/SUB",
                    [Consts.FM_INC] = "ADD/SUB", [Consts.FM_DEC] = "ADD/SUB",
                    [Consts.FM_CMP] = "CMP",
                    [Consts.FM_MUL] = "MUL"    , [Consts.FM_DIV] = "DIV" }
   for k,op in pairs (fam2op) do
      if (k == fam) then return op end
   end

   return "OTHER"
end

local function push_scalar_INT_arith_insns_breakdown (cqa_results)
   local t = {}
   for _,cat in ipairs ({"ADD/SUB", "CMP", "MUL", "DIV", "OTHER"}) do
      t [cat] = 0
   end

   local scalar_INT_insns = lookup_scalar_INT_insns (cqa_results)

   for _,insn in ipairs (scalar_INT_insns) do
      local op = get_scalar_INT_arith_op (insn)
      if (op ~= nil) then t[op] = t[op] + 1 end
   end

   cqa_results ["scalar INT arith insns"] = t
end

local function get_scalar_INT_logic_op (insn)
   if (insn:get_class() ~= Consts.C_LOGIC) then return nil end

   local fam = insn:get_family()
   local fam2op = { [Consts.FM_AND] = "AND", [Consts.FM_XOR  ] = "XOR",
                    [Consts.FM_OR ] = "OR" , [Consts.FM_SHIFT] = "SHIFT" }
   for k,v in pairs (fam2op) do
      if (k == fam) then return op end
   end

   return "OTHER"
end

local function push_scalar_INT_logic_insns_breakdown (cqa_results)
   local t = {}
   for _,cat in ipairs ({"AND", "XOR", "OR", "SHIFT"}) do
      t [cat] = 0
   end

   local scalar_INT_insns = lookup_scalar_INT_insns (cqa_results)

   for _,insn in ipairs (scalar_INT_insns) do
      local op = get_scalar_INT_logic_op (insn)
      if (op ~= nil) then t[op] = t[op] + 1 end
   end

   cqa_results ["scalar INT logic insns"] = t
end

local function push_nb_scalar_INT_other_insns (cqa_results)
   local sum = 0
   local scalar_INT_insns = lookup_scalar_INT_insns (cqa_results)

   for _,insn in ipairs (scalar_INT_insns) do
      if (get_scalar_INT_arith_op (insn) == nil and
          get_scalar_INT_logic_op (insn) == nil) then
         sum = sum + 1
      end
   end

   cqa_results ["nb scalar INT other insns"] = sum
end

local function push_nb_loop_control_insns (cqa_results)
   local sum = 0
   for _,insn in ipairs (cqa_results ["loop control instructions"]) do
      sum = sum + 1
   end

   cqa_results ["nb loop control insns"] = sum
end

-------------------------- SIMD INT -------------------------
-- TODO: use/update families
local function get_SIMD_INT_arith_op (insn_name)
   local find = string.find

   for _,op in ipairs ({"ADD", "SUB", "CMP", "MUL", "SAD"}) do
      if (find (insn_name, "^V?P"..op) ~= nil) then
         return op
      end
   end

   if (find (insn_name, "^V?PHADD") ~= nil) then return "ADD" end
   if (find (insn_name, "^V?PHSUB") ~= nil) then return "SUB" end
   if (find (insn_name, "^V?PMAD") ~= nil) then return "FMA" end
   if (find (insn_name, "^V?MPSAD") ~= nil) then return "SAD" end

   for _,op in ipairs ({"MIN", "MAX", "ABS", "SIGN"}) do
      if (find (insn_name, "^V?P"..op) ~= nil) then
         return "OTHER"
      end
   end

   return nil
end

local function push_SIMD_INT_arith_insns_breakdown (cqa_results)
   local t = {}
   for _,op in ipairs ({"ADD", "SUB", "CMP", "MUL", "FMA", "SAD", "OTHER"}) do
      -- Redmine 4950: potential JIT bug with nested anonymous arrays
      t[op] = { XMM = 0, YMM = 0, ZMM = 0 }
   end

   for _,insn in ipairs (cqa_results.insns) do
      local insn_name = string.upper (insn:get_name())

      local op = get_SIMD_INT_arith_op (insn_name)
      if (op ~= nil) then
         local suffix
         if     (insn:uses_XMM()) then suffix = "XMM"
         elseif (insn:uses_YMM()) then suffix = "YMM"
         elseif (insn:uses_ZMM()) then suffix = "ZMM"
         end

         t[op][suffix] = t[op][suffix] + 1
      end
   end

   t["ADD/SUB"] = {}
   for _,suffix in ipairs ({"XMM", "YMM", "ZMM"}) do
      t["ADD/SUB"][suffix] = t["ADD"][suffix] + t["SUB"][suffix]

      t["ADD"][suffix] = nil
      t["SUB"][suffix] = nil
   end
   t["ADD"] = nil
   t["SUB"] = nil

   cqa_results ["SIMD INT arith insns"] = t
end

-- TODO: use/update families
local function get_SIMD_INT_logic_op (insn_name)
   local find = string.find

   for _,op in ipairs ({"TEST", "AND", "ANDN", "XOR", "OR"}) do
      if (find (insn_name, "^V?P"..op) ~= nil) then
         return op
      end
   end

   if (find (insn_name, "^V?PS[LR]") ~= nil) then return "SHIFT" end

   return nil
end

local function push_SIMD_INT_logic_insns_breakdown (cqa_results)
   local t = {}
   for _,op in ipairs ({"TEST", "AND", "ANDN", "XOR", "OR", "SHIFT"}) do
      -- Redmine 4950: potential JIT bug with nested anonymous arrays
      t[op] = { XMM = 0, YMM = 0, ZMM = 0 }
   end

   local find = string.find

   for _,insn in ipairs (cqa_results.insns) do
      local insn_name = string.upper (insn:get_name())

      local op = get_SIMD_INT_logic_op (insn_name)
      if (op ~= nil) then
         local suffix
         if     (insn:uses_XMM()) then suffix = "XMM"
         elseif (insn:uses_YMM()) then suffix = "YMM"
         elseif (insn:uses_ZMM()) then suffix = "ZMM"
         end

         t[op][suffix] = t[op][suffix] + 1
      end
   end

   cqa_results ["SIMD INT logic insns"] = t
end

local function push_SIMD_INT_other_insns_breakdown (cqa_results)
   local t = { XMM = 0, YMM = 0, ZMM = 0 }

   local find = string.find

   for _,insn in ipairs (cqa_results.insns) do
      local insn_name = string.upper (insn:get_name())

      local op = get_SIMD_INT_arith_op (insn_name) or
         get_SIMD_INT_logic_op (insn_name)
      if (op ~= nil) then
         local suffix
         if     (insn:uses_XMM()) then suffix = "XMM"
         elseif (insn:uses_YMM()) then suffix = "YMM"
         elseif (insn:uses_ZMM()) then suffix = "ZMM"
         end

         t[suffix] = t[suffix] + 1
      end
   end

   cqa_results ["SIMD INT other insns"] = t
end
------------------------- FP -------------------------

local function push_FP_arith_insns_breakdown (cqa_results)
   -- Redmine 4950: potential JIT bug with nested anonymous arrays
   local regs_base = {"SS", "SD", "PS", "PD"}
   local regs_all = {"SS", "SD", "PS", "PD",
                     "PS-XMM", "PS-YMM", "PS-ZMM",
                     "PD-XMM", "PD-YMM", "PD-ZMM"}
   local ops = {"ADD", "SUB", "MUL", "FMA", "DIV", "SQRT", "RCP", "RSQRT"}
   local t = {}
   for _,op in ipairs (ops) do
      t[op] = {}
      for _,suffix in ipairs (regs_all) do
         t[op][suffix] = 0;
      end
   end

   local find = string.find

   for _,insn in ipairs (cqa_results.insns) do
      local insn_name = string.upper (insn:get_name())

      for _,op in ipairs (ops) do
         for _,suffix in ipairs (regs_base) do

            -- TODO: try to hoist this block
            if ((find (insn_name, "^V?"..op..suffix.."$") ~= nil) or
                (op == "FMA" and insn:is_fma() and find (insn_name, suffix.."$") ~= nil)) then
               t[op][suffix] = t[op][suffix] + 1

               if (suffix == "PS" or suffix == "PD") then
                  if     (insn:uses_XMM()) then suffix = suffix .. "-XMM"
                  elseif (insn:uses_YMM()) then suffix = suffix .. "-YMM"
                  elseif (insn:uses_ZMM()) then suffix = suffix .. "-ZMM"
                  end
                  t[op][suffix] = t[op][suffix] + 1
               end
            end
         end
      end
   end

   t["ADD/SUB"] = {}
   for _,suffix in ipairs (regs_all) do
      t["ADD/SUB"][suffix] = t["ADD"][suffix] + t["SUB"][suffix]

      t["ADD"][suffix] = nil
      t["SUB"][suffix] = nil
   end
   t["ADD"] = nil
   t["SUB"] = nil

   cqa_results ["FP arith insns"] = t
end

local function push_mem_insns_breakdown (cqa_results)
   local t = {}
   for _,v in ipairs ({"8 bits", "16 bits", "32 bits", "64 bits", "128 bits", "256 bits", "512 bits", "MOVH/LPS/D", "Unknown", "Other size"}) do
      t[v] = { ["loads"] = 0, ["stores"] = 0 }
   end

   local find = string.find

   for _,insn in ipairs (cqa_results.insns) do
      if (insn:is_load() or insn:is_store()) then
         local base;

         if (find (insn:get_name(), "MOV[LH]P[SD]") ~= nil) then
            base = "MOVH/LPS/D";
         else
            base = "Unknown";

            mem_oprnd = insn:get_first_mem_oprnd();

            if (mem_oprnd ~= nil) then
               if     (mem_oprnd ["size"] ==   8) then
                  base = "8 bits";
               elseif (mem_oprnd ["size"] ==  16) then
                  base = "16 bits";
               elseif (mem_oprnd ["size"] ==  32) then
                  base = "32 bits";
               elseif (mem_oprnd ["size"] ==  64) then
                  base = "64 bits";
               elseif (mem_oprnd ["size"] == 128) then
                  base = "128 bits";
               elseif (mem_oprnd ["size"] == 256) then
                  base = "256 bits";
               elseif (mem_oprnd ["size"] == 512) then
                  base = "512 bits";
               elseif (type (mem_oprnd ["size"]) == "number") then
                  base = "Other size";
               end
            end
         end

         if (insn:is_load()) then
            t [base]["loads"] = t [base]["loads"] + 1
         end

         if (insn:is_store()) then
            t [base]["stores"] = t [base]["stores"] + 1
         end
      end
   end

   cqa_results ["memory insns"] = t
end

local function push_SPDP_cvt_insns_breakdown (cqa_results)
   local t = {}
   for _,v in ipairs ({"SS2SD", "PS2PD-XMM", "PS2PD-YMM", "PS2PD-ZMM",
                       "SD2SS", "PD2PS-XMM", "PD2PS-YMM", "PD2PS-ZMM"}) do
      t[v] = 0
   end

   local find = string.find

   for _,insn in ipairs (cqa_results.insns) do
      local name = insn:get_name();

      if (find (name, "^V?CVT") ~= nil) then
         if (find (name, "SS2SD") ~= nil) then
            t ["SS2SD"] = t ["SS2SD"] + 1;

         elseif (find (name, "SD2SS") ~= nil) then
            t ["SD2SS"] = t ["SD2SS"] + 1;

         elseif (find (name, "PS2PD") ~= nil) then
            if (insn:uses_ZMM()) then
               t ["PS2PD-ZMM"] = t ["PS2PD-ZMM"] + 1;
            elseif (insn:uses_YMM()) then
               t ["PS2PD-YMM"] = t ["PS2PD-YMM"] + 1;
            elseif (insn:uses_XMM()) then
               t ["PS2PD-XMM"] = t ["PS2PD-XMM"] + 1;
            end

         elseif (find (name, "PD2PS") ~= nil) then
            if (insn:uses_ZMM()) then
               t ["PD2PS-ZMM"] = t ["PD2PS-ZMM"] + 1;
            elseif (insn:uses_YMM()) then
               t ["PD2PS-YMM"] = t ["PD2PS-YMM"] + 1;
            elseif (insn:uses_XMM()) then
               t ["PD2PS-XMM"] = t ["PD2PS-XMM"] + 1;
            end
         end
      end
   end

   cqa_results ["SP/DP conversion instructions"] = t
end

-- TODO improve this
local function reg_is_SIMD (reg)
   return (string.find (reg.value, "[XYZ]MM") ~= nil)
end

local function push_bytes_moved_GP (cqa_results)
   local t = { data = { read = 0, write = 0 },
               addr = { read = 0, write = 0 } }

   -- Addresses are part of memory operands
   local addr_regs = {}
   for _,insn in ipairs (cqa_results.insns) do
      for _,oprnd in ipairs (insn:get_operands()) do
         if (oprnd.type == Consts.OT_MEMORY) then
            for _,sub_oprnd in pairs (oprnd.value) do
               if (sub_oprnd.type == Consts.OT_REGISTER) then
                  addr_regs [sub_oprnd.value] = true
               end
            end
         end
      end
   end

   local function _push_bytes_moved_reg (reg, tab)
      if (reg.read ) then tab.read  = tab.read  + (reg.size / 8) end
      if (reg.write) then tab.write = tab.write + (reg.size / 8) end
   end

   for _,insn in ipairs (cqa_results.insns) do
      for _,oprnd in ipairs (insn:get_operands()) do
         if (oprnd.type == Consts.OT_REGISTER and not reg_is_SIMD (oprnd)) then
            if (addr_regs [oprnd.value]) then
               _push_bytes_moved_reg (oprnd, t.addr)
            else
               _push_bytes_moved_reg (oprnd, t.data)
            end
         elseif (oprnd.type == Consts.OT_MEMORY) then
            for _,sub_oprnd in pairs (oprnd.value) do
               if (sub_oprnd.type == Consts.OT_REGISTER and not reg_is_SIMD (sub_oprnd)) then
                  if (sub_oprnd.read ) then t.addr.read  = t.addr.read  + (oprnd.size / 8) end
                  if (sub_oprnd.write) then t.addr.write = t.addr.write + (oprnd.size / 8) end
               end
            end
         end
      end
   end

   cqa_results ["bytes moved GP registers"] = t
end

local function push_bytes_moved_SIMD (cqa_results)
   local t = { read = 0, write = 0 }

   for _,insn in ipairs (cqa_results.insns) do
      local used_bytes = insn:get_read_bits() / 8
      for _,oprnd in ipairs (insn:get_operands()) do
         if (oprnd.type == Consts.OT_REGISTER and reg_is_SIMD (oprnd)) then
            if (oprnd.read ) then t.read  = t.read  + used_bytes end
            if (oprnd.write) then t.write = t.write + used_bytes end
         end
      end
   end

   cqa_results ["bytes moved SIMD registers"] = t
end

local ia32_x86_64 = { "ia32", "x86_64" }

__cqa_user_data = {
   requested_metrics = { 
      "function name", "addr", "src file", "src line min-max",
      "id", "can be analyzed", "nb paths",
      "unroll info", "unroll confidence level",
      "is main/unrolled", "unroll factor", "path ID", "repetitions",
      "extra_unroll_factor",
      "nb instructions", "nb uops", "loop length", "used x86 registers", "used mmx registers",
      "used xmm registers", "used ymm registers", "nb stack references", "pattern string",
      "[ia32_x86_64] pattern", "scalar INT arith insns", "scalar INT logic insns",
      "nb scalar INT other insns", "[ia32_x86_64] SIMD INT arith insns",
      "[ia32_x86_64] SIMD INT logic insns", "[ia32_x86_64] SIMD INT other insns",
      "nb loop control insns", "[ia32_x86_64] FP arith insns", "[ia32_x86_64] memory insns",
      "ADD-SUB / MUL ratio", "fit in cache", "assumed macro fusion",
      "scalar INT ops", "nb scalar INT operations",
      "SIMD INT ops", "nb SIMD INT operations",
      "FP ops", "nb total FP operations",
      "nb pure loads", "nb impl loads", "nb stores",
      "bytes prefetched", "bytes loaded", "bytes stored",
      "bytes moved if vectorized",
      "bytes loaded or stored", "bytes wasted", "arithmetic intensity", "arithmetic intensity extra info",
      "cycles instruction fetch", "cycles predecoding",
      "cycles instruction queue", "cycles decoding", "cycles micro-operation queue",
      "cycles ROB-read", "[ia32_x86_64] cycles front end", "dispatch",
      "cycles dispatch", "RecMII",
      "packed ratio INT", "packed ratio FP", "packed ratio",
      "vec eff ratio INT", "vec eff ratio FP", "vec eff ratio",
      "[ia32_x86_64] cycles", "scalar INT operations per cycle", "SIMD INT operations per cycle",
      "FP operations per cycle", "instructions per cycle",
      "bytes prefetched per cycle", "bytes loaded per cycle",
      "bytes stored per cycle", "bytes loaded or stored per cycle",
      "cycles L1 if fully vectorized", "cycles L1 if nomem vectorized",
      "cycles L1 if FP arith vectorized", "cycles if clean",
      "cycles if only FP", "cycles if only FP arith", "SP/DP conversion instructions",
      "bytes moved GP registers", "bytes moved SIMD registers",
   },

   path_metrics = {
      ["bytes wasted"] = {
         CSV_header = "Bytes wasted",
         desc = "Number of bytes wasted by using packed instructions as scalar ones"..
            "(typically ANDPS to compute absolute values of FP values)",
         lua_type = "number",
         arch = ia32_x86_64,
         compute = function (crp)
            local find = string.find
            local wasted_bytes = 0;

            for rank,insn in ipairs (crp.insns) do
               local is_packed_used_as_scalar = (find (insn:get_name(), "ANDP[SD]") ~= nil)

               if (is_packed_used_as_scalar and
                   insn:get_first_mem_oprnd () ~= nil) then
                  wasted_bytes = wasted_bytes + get_wasted_bytes (crp.insns, rank)
               end
            end

            crp ["bytes wasted"] = wasted_bytes
         end
      },

      ["scalar INT arith insns"] = {
         args = { {"ADD/SUB", "CMP", "MUL", "OTHER"} },
         CSV_header = "Nb scalar INT arith insn: %s",
         desc = "Integer arithmetic scalar instructions breakdown. Loop control instructions excluded",
         lua_type = "table",
         arch = ia32_x86_64,
         compute = push_scalar_INT_arith_insns_breakdown
      },

      ["scalar INT logic insns"] = {
         args = { {"AND", "XOR", "OR", "SHIFT"} },
         CSV_header = "Nb scalar INT logic insn: %s",
         desc = "Integer logic scalar instructions breakdown. Loop control instructions excluded",
         lua_type = "table",
         arch = ia32_x86_64,
         compute = push_scalar_INT_logic_insns_breakdown
      },

      ["nb scalar INT other insns"] = {
         CSV_header = "Nb INT other insns",
         desc = "Number of other integer scalar instructions. Loop control instructions excluded",
         lua_type = "number",
         compute = push_nb_scalar_INT_other_insns
      },

      ["nb loop control insns"] = {
         CSV_header = "Nb loop control insns",
         desc = "Number of loop control instructions",
         lua_type = "number",
         deps = { "loop control instructions" },
         compute = push_nb_loop_control_insns
      },
      ["[ia32_x86_64] SIMD INT arith insns"] = {
         args = { {"ADD/SUB", "CMP", "MUL", "FMA", "SAD", "OTHER"},
                  {"XMM", "YMM", "ZMM"} },
         CSV_header = "Nb SIMD INT arith insn: %s-%s",
         desc = "Integer arithmetic SIMD instructions breakdown",
         lua_type = "table",
         arch = ia32_x86_64,
         compute = push_SIMD_INT_arith_insns_breakdown
      },

      ["[ia32_x86_64] SIMD INT logic insns"] = {
         args = { {"TEST", "AND", "ANDN", "XOR", "OR", "SHIFT"},
                  {"XMM", "YMM", "ZMM"} },
         CSV_header = "Nb SIMD INT logic insn: %s-%s",
         desc = "Integer logic SIMD instructions breakdown",
         lua_type = "table",
         arch = ia32_x86_64,
         compute = push_SIMD_INT_logic_insns_breakdown
      },

      ["[ia32_x86_64] SIMD INT other insns"] = {
         args = { {"XMM", "YMM", "ZMM"} },
         CSV_header = "Nb SIMD INT other insn: %s",
         desc = "Integer other SIMD instructions breakdown",
         lua_type = "number",
         arch = ia32_x86_64,
         compute = push_SIMD_INT_other_insns_breakdown
      },

      ["[ia32_x86_64] FP arith insns"] = {
         args = { {"ADD/SUB", "MUL", "FMA", "DIV", "SQRT", "RCP", "RSQRT"},
                  {"SS", "SD", "PS-XMM", "PS-YMM", "PS-ZMM", "PD-XMM", "PD-YMM", "PD-ZMM"} },
         CSV_header = "Nb FP insn: %s%s",
         desc = "FP arithmetic instructions breakdown",
         lua_type = "table",
         arch = ia32_x86_64,
         compute = push_FP_arith_insns_breakdown
      },

      ["[ia32_x86_64] memory insns"] = {
         args = { {"8 bits", "16 bits", "32 bits", "64 bits", "128 bits", "256 bits", "512 bits", "MOVH/LPS/D"},
                  {"loads", "stores"}},
         CSV_header = "Nb %s %s",
         desc = "Memory instructions breakdown",
         lua_type = "table",
         arch = ia32_x86_64,
         compute = push_mem_insns_breakdown
      },

      ["SP/DP conversion instructions"] = {
         args = { {"SS2SD", "PS2PD-XMM", "PS2PD-YMM", "PS2PD-ZMM",
                   "SD2SS", "PD2PS-XMM", "PD2PS-YMM", "PD2PS-ZMM" } },
         CSV_header = "Nb insn: %s",
         desc = "SP/DP Conversion instructions breakdown",
         lua_type = "table",
         compute = push_SPDP_cvt_insns_breakdown
      },

      ["bytes moved GP registers"] = {
         args = { {"data", "addr"},
                  {"read", "write"} },
         CSV_header = "Bytes GP: %s %s",
         desc = "Bytes moved from/to GP registers",
         lua_type = "table",
         arch = ia32_x86_64,
         compute = push_bytes_moved_GP
      },

      ["bytes moved SIMD registers"] = {
         args =	{ {"read", "write"} },
         CSV_header = "Bytes SIMD: %s",
         desc = "Bytes moved from/to SIMD registers",
         lua_type = "table",
         arch = ia32_x86_64,
         compute = push_bytes_moved_SIMD
      },
   }
}
