proj = project.new ("foo");
local args = Utils:get_args(arg);

binary = args.binary
uarch = args.uarch
loop_id = args.loop_id


function DEC_HEX (IN)
    local B, K, OUT, I, D=16, "0123456789abcdef", "", 0
    while IN > 0 do
        I = I + 1
        IN, D = math.floor (IN / B), math.mod (IN, B) + 1
        OUT = string.sub (K,D,D) .. OUT
    end
    return OUT
end

function pad (string, nb)
	local pad_string = "", i, tab_size, floored_div_res, tmp_string

	tab_size = 8
	tmp_string = string . gsub (string, "\t", " ")
	floored_div_res = math . floor (tmp_string : len () / tab_size)

	i = floored_div_res

	for i = i, nb
	do
		pad_string = pad_string .. "\t"
	end

	return tmp_string .. pad_string
end

if (binary == nil or uarch == nil or loop_id == nil)
then
	print ("Missing argument!");
	return -1;
end

if (uarch ~= "sandy_bridge" and uarch ~= "ivy_bridge" and uarch ~= "haswell")
then
	print ("Wrong architecture! [" .. uarch .. "]");
	return -1;
end

if (uarch == "sandy_bridge") then uarch_c = Consts.x86_64.UARCH_SANDY_BRIDGE end
if (uarch == "ivy_bridge") then uarch_c = Consts.x86_64.UARCH_IVY_BRIDGE end
if (uarch == "haswell") then uarch_c = Consts.x86_64.UARCH_HASWELL end

bin = proj:load (binary, uarch_c)


function count (table)
	local res = 0

	if (table ~= nil)
	then
		for _ in pairs (table) do res = res + 1 end
	end

	return res
end

function get_fe_uops (instr)
	local res = 1, disp

	disp = instr:get_dispatch ()

	if (disp ~= nil)
	then
		res = disp ["nb_uops"]["max"]
	end

	return res
end

function get_nb_components (instr)
	local res = 0, disp

	disp = instr:get_dispatch ()

	if (disp ~= nil)
	then
		res = count (disp ["uops_groups"])
		if (is_avx_div (instr))
		then
			if (instr : is_load ())
			then
				res = res + 2
			else
				res = res + 1
			end
		end
	end

	return res
end

function get_component_type (instr, pos)
	local res = "weird", disp

	if (instr:is_load ())
	then
		if (pos == 1)
		then
			res = "load"
		else
			res = "compute"
		end
	else if (instr:is_store ())
	then
		if (pos == 1)
		then
			res = "store_addr"
		else
			res = "store"
		end
	else if (instr:is_branch ())
	then
		res = "branch"
	else if (get_nb_components (instr) == 0)
	then
		res = "nop"
	else
		res = "compute"
	end
	end
	end
	end

	return res
end

function get_edited_register_name (name)
	local res = ""

	res = name

	if (string.match (name, 'R%d+D$') ~= nil)
	then
		res = string.sub (res, 1, -2)
	end

	return res
end

function get_memory_operands (operands)
	local res = "", operand, id, id2, id3, value, values, reg_name

	if (operands ~= nil)
	then
		for id in pairs (operands)
		do
			operand = operands [id]
			if (operand ["type"] == MDSAPI.MEMORY)
			then
				values = operand ["value"]
				for id2 in pairs (values)
				do
					value = values [id2]
					if (value ["type"] == MDSAPI.REGISTER)
					then
						reg_name = get_edited_register_name (value ["value"])
						if (res == "") then res = reg_name else res = res .. "," .. reg_name end
					end
				end
			end
		end
	end

	return res
end

function modifies_test_bit (instr)
	local res = false

	if (	instr : get_name () == "ADD" or
		instr : get_name () == "SUB" or
		instr : get_name () == "NEG" or
		instr : get_name () == "CMP" or
		instr : get_name () == "INC" or
		instr : get_name () == "DEC"
		)
	then
		res = true
	end

	return res
end

function get_compute_operands (operands, rw)
	local res = "", operand, id, value, reg_name

	if (operands ~= nil)
	then
		for id in pairs (operands)
		do
			operand = operands [id]
			if (operand ["type"] == MDSAPI.REGISTER)
			then
				if (operand ["type"] == MDSAPI.REGISTER and operand [rw])
				then
					reg_name = get_edited_register_name (operand ["value"])
					if (res == "") then res = reg_name else res = res .. "," .. reg_name end
				end
			end
		end
	end

	return res
end

function get_component_inputs (instr, pos)
	local res, disp, comp_type, operands

	comp_type = get_component_type (instr, pos)
	operands = instr : get_operands ()

	if ((instr : get_name () == "XORPS" or instr : get_name () == "XORPD" or instr : get_name () == "VXORPD" or instr : get_name () == "VXORPS") and comp_type == "nop")
	then
		res = ""
	elseif (comp_type == "load" or instr:get_name () == "LEA")
	then
		res = get_memory_operands (operands)
	elseif (comp_type == "compute")
	then
		res = get_compute_operands (operands, "read")
	elseif (comp_type == "store_addr")
	then
		res = get_memory_operands (operands)
	elseif (comp_type == "store")
	then
		res = get_compute_operands (operands, "read")
	elseif (comp_type == "branch")
	then
		res = get_compute_operands (operands, "read")
		if (res == "") then res = "test" else res = res .. ",test" end
	elseif (comp_type == "nop")
	then
		res = get_compute_operands (operands, "read")
	else
		res = "?"
	end

	return res
end

function get_component_outputs (instr, pos)
	local res = "", disp, comp_type

	comp_type = get_component_type (instr, pos)

	if (comp_type == "load")
	then
		operands = instr : get_operands ()
		res = get_compute_operands (operands, "write")
	elseif (comp_type == "compute")
	then
		-- might need to modify "test" if integer op
		operands = instr : get_operands ()
		if (instr : get_name () == "CMP") then res = "" else res = get_compute_operands (operands, "write") end
		if (modifies_test_bit (instr))
		then
			if (res == "") then res = "test" else res = res .. ",test" end
		end
	elseif (comp_type == "store_addr")
	then
		res = ""
	elseif (comp_type == "store")
	then
		res = ""
	elseif (comp_type == "branch")
	then
		res = ""
	elseif (comp_type == "nop")
	then
		operands = instr : get_operands ()
		res = get_compute_operands (operands, "write")
	else
		res = "?"
	end

	return res
end

function get_component_latency (instr, pos)
	local res = "", disp, comp_type

	comp_type = get_component_type (instr, pos)

	if (comp_type == "load")
	then
		res = "4"
	elseif (comp_type == "compute")
	then
		res = instr : get_dispatch () ["latency"]["max"]
		if (is_avx_div (instr))
		then
			if ((get_fe_uops (instr) == 3 and pos == 1) or (get_fe_uops (instr) == 4 and pos == 2))
			then
				res = math.ceil (res / 2)
			else
				res = math.floor (res / 2)
			end
		end
	elseif (comp_type == "store_addr")
	then
		res = "1"
	elseif (comp_type == "store")
	then
		res = "3"
	elseif (comp_type == "branch")
	then
		res = "1"
	elseif (comp_type == "nop")
	then
		res = "0"
	else
		res = "?"
	end

	return res
end

function get_component_nb_uops (instr, pos)
	local res = 1, i, ports, disp, uop_groups, id, uop_group, units, cpt

	if (disp ~= nil)
	then
		uop_groups = disp ["uops_groups"]
		for id in pairs (uop_groups)
		do
			if (id == pos)
			then
				uop_group = uop_groups [id]
				units = uop_group ["units"]

				for id2 in pairs (units)
				do
					cpt = units [id2]
					if (cpt == "x") then cpt = 1 end
					--print ("\n" .. id2 .. ": " .. units [id2])
					res = math.max (res, cpt)
				end
			end
		end
	end
	
	return res
	
end

function get_compute_component_eligible_ports (instr, pos)
	local res = "", i, ports, disp, uop_groups, id, uop_group, units, cpt

	ports = {0, 0, 0, 0, 0, 0, 0}
	saved_ports = {0, 0, 0, 0, 0, 0, 0}
	cpt = pos

	disp = instr:get_dispatch ()

	if (disp ~= nil)
	then
		uop_groups = disp ["uops_groups"]
		for id in pairs (uop_groups)
		do
			if (cpt >= pos)
			then
				for i = 1, 8, 1	do ports [i] = 0 end

				uop_group = uop_groups [id]
				units = uop_group ["units"]

				for id2 in pairs (units)
				do
					--print ("\n" .. id2 .. ": " .. units [id2])
					ports [units [id2] + 1] = "x"
				end

				cpt = cpt - 1
												-- TODO: check if it works as intended for instructions with several components
				if (ports [3] == 0 and ports [4] == 0 and ports [5] == 0)
				then
					for i = 1, 8, 1	do saved_ports [i] = ports [i] end
				end
			end
		end
	end

	for i = 1, 8, 1
	do
		if (i ~= 1) then res = res .. ' ,' end
		res = res .. saved_ports [i]
		--print ("Debug: " .. res)
	end

	return res
end

function is_macrofused (instr)
	local res = false, next_instr

	next_instr = instr: get_next ()

	if (get_nb_components (instr) == 1 and get_nb_components (next_instr) == 1)
	then
		if (get_component_type (instr, 1) == "compute" and modifies_test_bit (instr) and get_component_type (next_instr, 1) == "branch")
		then
			res = true
		end
	end

	return res
end

function is_avx_div (instr)
	local res = false

	if (instr : get_name () == "VDIVPS" or instr : get_name () == "VDIVPD" or instr : get_name () == "VSQRTPS" or instr : get_name () == "VSQRTPD")
	then
		res = true
	end

	return res
end

function was_macrofused (instr)
	local res = false, prev_instr

	prev_instr = instr: get_prev ()

	if (get_nb_components (instr) == 1 and get_nb_components (prev_instr) == 1)
	then
		if (get_component_type (prev_instr, 1) == "compute" and modifies_test_bit (prev_instr) and get_component_type (instr, 1) == "branch")
		then
			res = true
		end
	end

	return res
end

function get_component_port_use (instr, pos)
	local res = "", disp, comp_type

	comp_type = get_component_type (instr, pos)

	if (comp_type == "load")
	then
		res = "0 ,0 ,x ,x ,0 ,0 ,0 ,0"
	elseif (comp_type == "store_addr")
	then
		res = "0 ,0 ,x ,x ,0 ,0 ,0 ,0"
	elseif (comp_type == "store")
	then
		res = "0 ,0 ,0 ,0 ,1 ,0 ,0 ,0"
	elseif (comp_type == "branch" or is_macrofused (instr))
	then
		res = "0 ,0 ,0 ,0 ,0 ,1 ,0 ,0"
	elseif (comp_type == "compute")
	then
		--res = "? ,? ,0 ,0 ,0 ,? ,0 ,0"
		res = get_compute_component_eligible_ports (instr, pos)
	elseif (comp_type == "nop")
	then
		res = "0 ,0 ,0 ,0 ,0 ,0 ,0 ,0"
	else
		res = "? ,? ,? ,? ,? ,? ,? ,?"
	end

	return res
end

function get_component_special (instr, pos)
	local res = "", disp, comp_type, nb

	comp_type = get_component_type (instr, pos)

	if (comp_type == "load")
	then
		if (instr : uses_YMM ())
		then
			res = "avx_mem:2"
		end
	elseif (comp_type == "compute")
	then
		if (get_component_latency (instr, pos) > 7)
		then
			--nb = get_component_latency (instr, pos) - 1
			nb = get_component_latency (instr, pos)
			if (is_avx_div (instr))
			then
				if ((get_fe_uops (instr) == 3 and pos == 1) or (get_fe_uops (instr) == 4 and pos == 2))
				then
					nb = nb + 1
				else
					nb = nb - 1
				end
			end
			if (uarch_c == Consts.x86_64.UARCH_HASWELL)
			then
				if (nb <= 15)
				then
					nb = 7
				else
					nb = 14
				end
			end
			res = "divider:" .. nb
		end
	elseif (comp_type == "store_addr")
	then
		res = ""
	elseif (comp_type == "store")
	then
		if (instr : uses_YMM ())
		then
			res = "avx_mem:2"
		end
	elseif (comp_type == "branch")
	then
		res = ""
	elseif (comp_type == "nop")
	then
		res = ""
	else
		res = "?"
	end

	return res
end



print ("instruction;						nb_fe;	type;		inputs;		outputs;	latency;	P0,P1,P2,P3,P4,P5,P6,P7;	special;	type;		inputs;		outputs;	latency;	P0,P1,P2,P3,P4,P5,P6,P7;	special;");
for current_function in bin:functions () do
	for l in current_function:loops () do
		lid = l:get_id ()
		if (lid == "all" or tonumber (loop_id) == lid)
		then
			for b in l:blocks() do
				for instr in b:instructions () do
					if (not was_macrofused (instr))
					then
						to_disp = DEC_HEX (instr:get_address ()) .. ":  " .. string.sub (instr:tostring (), 7)
						if (is_macrofused (instr)) then to_disp = to_disp .. " : " .. instr : get_next () : get_name () end
						to_disp = to_disp .. ";"
						io.write (pad (to_disp, 6))

						io.write (pad (get_fe_uops (instr) .. ";", 0))

						nb_components = math.max (get_nb_components (instr), 1)

						for i = 1, nb_components, 1
						do
							--uops_for_this_component = get_component_nb_uops (instr, i)
							--for j = 1, uops_for_this_component, 1
							--do
						
							if (is_avx_div (instr) and i == nb_components)
							then
								io.write (pad ("compute" .. ";", 1))
								io.write (pad ("" .. ";", 1))
								io.write (pad ("" .. ";", 1))
								io.write (pad ("1" .. ";", 1))
								io.write (pad (" , , , , , x, , " .. ";", 3))
								io.write (pad ("" .. ";", 1))								
							else
								type = get_component_type (instr, i)
								if (is_macrofused (instr)) then type = "branch" end
								io.write (pad (type .. ";", 1))

								reg_inputs = get_component_inputs (instr, i)
								io.write (pad (reg_inputs .. ";", 1))

								reg_outputs = get_component_outputs (instr, i)
								io.write (pad (reg_outputs .. ";", 1))

								latency = get_component_latency (instr, i)
								io.write (pad (latency .. ";", 1))

								port_use = get_component_port_use (instr, i)
								io.write (pad (port_use .. ";", 3))

								special = get_component_special (instr, i)
								io.write (pad (special .. ";", 1))
							end
						end
						io.write ("\n")
					end
				end
			end
		end
	end 
end
