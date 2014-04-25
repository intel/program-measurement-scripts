--
-- Create the root (project) of the hierarchy
--
proj = project.new ("my_first_MAQAO_analysis");
--
-- parse the argument sent through the command line
--
local args = Utils:get_args(arg);
binary_name = args.binary_name;
funct_name = args.funct_name;
lid = args.lid;
--
-- Create the binary object. The Load function, call the disassembler and feed the internal represention of MAQAO
-- with all the relevant information
--
bin = proj:load (binary_name, 0); 
-- 
-- Parse the binary file passed as argument
--

function DEC_HEX(IN)
    local B,K,OUT,I,D=16,"0123456789abcdef","",0
    while IN>0 do
        I=I+1
        IN,D=math.floor(IN/B),math.mod(IN,B)+1
        OUT=string.sub(K,D,D)..OUT
    end
    return OUT
end


for current_function in bin:functions () do
	-- in LUA .. means concatenate
	id=0
	name="N/A"
	--print("Function name: "..current_function:tostring())

	for word in current_function:tostring():gmatch("[a-zA-Z0-9_]+") do
		if (id == 1) then
			name=word
			break
		end
		id=id+1
	end

	--print("Deduced name: "..name)

--	if (funct_name == name) then
--		print ("Found function '"..funct_name.."' ("..current_function:tostring()..")")
		for l in current_function:loops () do
			loop_id=l:get_id ()
			if (lid == "all" or tonumber(lid) == loop_id) then
				--print("Loop number: "..loop_id)
				for b in l:blocks() do
					for instr in b:instructions () do
						-- dump the instruction with a small indentation
						print(DEC_HEX(instr:get_address())..":  "..string.sub(instr:tostring(), 7))
					end
				end
			end
		end 
--	end
end
--print ("End of analysis for binary "..binary_name)

