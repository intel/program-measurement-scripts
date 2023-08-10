#include <bfd.h>
#include <stdint.h> // uint64_t

typedef struct {
   const void *start;
   const void *end;
   unsigned long offset;
   const char *name;

   bfd *bfd_image;
   asymbol **bfd_image_symbols;
} map_t;

typedef struct {
   char *module_name;
   uint64_t module_offset;
   char *fct_name;
   char *fct_demangled_name;
   char *src_file;
   unsigned src_line;
} resolved_codeptr_t;

typedef struct {
   map_t *maps;
   unsigned nb_maps;
} ompt_tool_addr2line_context_t;

void ompt_tool_addr2line_init (ompt_tool_addr2line_context_t *a2l_ctxt);

void ompt_tool_addr2line_get (const ompt_tool_addr2line_context_t *a2l_ctxt,
                              const void *codeptr_ra, resolved_codeptr_t *rc);

void ompt_tool_addr2line_destroy (ompt_tool_addr2line_context_t *a2l_ctxt);
