---
--  Copyright (C) 2004 - 2018 Université de Versailles Saint-Quentin-en-Yvelines (UVSQ)
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

local function push_arith_insns_breakdown (cqa_results)
   local t = {}
   for _,op in ipairs ({"ADD", "SUB", "MUL", "FMA", "DIV", "SQRT", "RCP", "RSQRT"}) do
      t[op] = {}
      for _,suffix in ipairs ({"SS", "SD", "PS", "PD", "PS-XMM", "PS-YMM", "PS-ZMM", "PD-XMM", "PD-YMM", "PD-ZMM"}) do
         t[op][suffix] = 0;
      end
   end

   local find = string.find

   for _,insn in ipairs (cqa_results.insns) do
      local insn_name = string.upper (insn:get_name())

      for _,op in ipairs ({"ADD", "SUB", "MUL", "FMA", "DIV", "SQRT", "RCP", "RSQRT"}) do
         for _,suffix in ipairs ({"SS", "SD", "PS", "PD"}) do

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
   for _,suffix in ipairs ({"SS", "SD", "PS", "PD", "PS-XMM", "PS-YMM", "PS-ZMM", "PD-XMM", "PD-YMM", "PD-ZMM"}) do
      t["ADD/SUB"][suffix] = t["ADD"][suffix] + t["SUB"][suffix]

      t["ADD"][suffix] = nil
      t["SUB"][suffix] = nil
   end
   t["ADD"] = nil
   t["SUB"] = nil

   cqa_results ["arith insns"] = t
end

local function push_mem_insns_breakdown (cqa_results)
   local t = {}
   for _,v in ipairs ({"8 bits", "16 bits", "32 bits", "64 bits", "128 bits", "256 bits", "512 bits", "MOVH/LPS/D"}) do
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
               if     (mem_oprnd ["size"] ==  8) then
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

local ia32_x86_64 = { "ia32", "x86_64" }

__cqa_user_data = {
   requested_metrics = { 
      "function name", "addr", "src file", "src line min-max",
      "id", "can be analyzed", "nb paths",
      "unroll info", "unroll confidence level",
      "is main/unrolled", "unroll factor", "path ID",
      "extra_unroll_factor",
      "nb instructions", "nb uops", "loop length", "used x86 registers", "used mmx registers",
      "used xmm registers", "used ymm registers", "nb stack references", "pattern string",
      "[ia32_x86_64] pattern", "[ia32_x86_64] arith insns", "[ia32_x86_64] memory insns",
      "ADD-SUB / MUL ratio", "fit in cache", "assumed macro fusion",
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
      "[ia32_x86_64] cycles", "FP operations per cycle", "instructions per cycle",
      "bytes prefetched per cycle", "bytes loaded per cycle",
      "bytes stored per cycle", "bytes loaded or stored per cycle",
      "cycles L1 if fully vectorized", "cycles L1 if nomem vectorized",
      "cycles L1 if FP arith vectorized", "cycles if clean",
      "cycles if only FP", "cycles if only FP arith",
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

      ["[ia32_x86_64] arith insns"] = {
         args = { {"ADD/SUB", "MUL", "FMA", "DIV", "SQRT", "RCP", "RSQRT"},
                  {"SS", "SD", "PS-XMM", "PS-YMM", "PS-ZMM", "PD-XMM", "PD-YMM", "PD-ZMM"} },
         CSV_header = "Nb insn: %s%s",
         desc = "Arithmetic instructions breakdown",
         lua_type = "table",
         arch = ia32_x86_64,
         compute = push_arith_insns_breakdown
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
   }
}
