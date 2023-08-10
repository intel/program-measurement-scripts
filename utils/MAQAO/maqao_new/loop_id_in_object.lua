proj = project.new ("my_first_MAQAO_analysis");

local args = Utils:get_args(arg);
binary_name = args.binary_name;
loop_id = tonumber (args.loop_id);
object_name = args.object_name;

bin = proj : load (binary_name, 0);
obj = proj : load (object_name, 0);

function get_address (loop)
	local first_block
	local first_insn
	local res

	for first_block in loop : blocks ()
	do
		for first_insn in first_block : instructions ()
		do
			return first_insn : get_address ()			
		end
	end
end

for current_function in bin : functions ()
do
	for l in current_function : loops ()
	do
		if (loop_id == l : get_id ())
		then
			original_function_name = current_function : get_name ()
			original_loop_address = get_address (l)
			original_function_address = get_address (current_function)
			original_loop_offset = original_loop_address - original_function_address

			--print ('Original loop: ' .. original_loop_address .. ' [' .. original_function_name .. ', ' .. original_function_address .. '] => ' .. original_loop_offset )
		end
	end 
end

for current_function in obj : functions ()
do
	object_function_name = current_function : get_name ()

	if (object_function_name == original_function_name)
	then
		object_function_address = get_address (current_function)
		for l in current_function : loops ()
		do
			object_loop_address = get_address (l)
			object_loop_offset = object_loop_address - object_function_address

			--print ('Object loop: ' .. object_loop_address .. ' [' .. object_function_name .. ', ' .. object_function_address .. '] => ' .. object_loop_offset )

			if (object_loop_offset == original_loop_offset)
			then
				print (l : get_id ())	
			end
		end
	end
end
