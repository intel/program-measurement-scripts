---
--  Copyright (C) 2004 - 2020 Université de Versailles Saint-Quentin-en-Yvelines (UVSQ)
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

local ia32_x86_64 = { "ia32", "x86_64" }

__cqa_user_data = {
   requested_metrics = { 
      "function name", "addr", "src file", "src line min-max",
      "id", "can be analyzed", "nb paths",
      "unroll info", "unroll confidence level",
      "is main/unrolled", "unroll factor", "path ID", "repetitions",
      "extra_unroll_factor",
      "nb instructions", "nb uops", "loop length", "used x86 registers", "used mmx registers",
      "used xmm registers", "used ymm registers", "used zmm registers", "nb stack references",
      "scalar INT arith insns", "scalar INT logic insns",
      "nb scalar INT other insns", "[ia32_x86_64] SIMD INT arith insns",
      "[ia32_x86_64] SIMD INT logic insns", "[ia32_x86_64] SIMD INT other insns",
      "nb loop control insns", "[ia32_x86_64] FP arith insns", "[ia32_x86_64] memory insns",
      "fit in cache", "assumed macro fusion",
      "scalar INT ops", "nb scalar INT operations",
      "SIMD INT ops", "nb SIMD INT operations",
      "FP ops", "nb total FP operations",
      "nb pure loads", "nb impl loads", "nb stores",
      "bytes prefetched", "bytes loaded", "bytes stored",
      "bytes moved if vectorized",
      "bytes loaded or stored", "bytes wasted",
      "cycles instruction fetch", "cycles predecoding",
      "cycles instruction queue", "cycles decoding", "cycles micro-operation queue",
      "cycles ROB-read", "[ia32_x86_64] cycles front end", "dispatch",
      "cycles dispatch", "RecMII",
      "packed ratio INT", "packed ratio FP", "packed ratio", "packing instructions",
      "vec eff ratio INT", "vec eff ratio FP", "vec eff ratio",
      "[ia32_x86_64] cycles",
      "cycles L1 if fully vectorized", "cycles L1 if nomem vectorized",
      "cycles L1 if FP arith vectorized", "cycles if clean",
      "cycles if only FP", "cycles if only FP arith",
      "SP/DP conversion instructions", "INT/FP conversion instructions",
      "bytes moved GP registers", "bytes moved SIMD registers", "streams stride nb",
   },

   path_metrics = {}
}
