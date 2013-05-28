--
-- Create the root (project) of the hierarchy
--
proj = project.new ("my_first_MAQAO_analysis");
--
-- parse the argument sent through the command line
--
local args = utils:get_args(arg);
binary_name = args.binary_name;
loop_address = args.loop_address;

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

--print ("Program '" .. binary_name .. "' Loop address = '" .. loop_address .. "'")

for current_function in bin:functions () do

	--for l in current_function:loops () do
		--for b in l:blocks() do
		for b in current_function:blocks() do
			first_ins = b:get_first_insn ();
			if (first_ins ~= nil) then
				if (DEC_HEX(first_ins:get_address()) == loop_address) then

					our_block = b:get_successors () [1]
	
					for instr in our_block:instructions () do
						-- dump the instruction with a small indentation
						print(DEC_HEX(instr:get_address())..":  "..string.sub(instr:tostring(), 7))
					end
					return
				end
			end
		end
	--end
end

print ("Unhappy :(")


