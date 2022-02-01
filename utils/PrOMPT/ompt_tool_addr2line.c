#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include <bfd.h>
#include <libiberty/demangle.h> // use <demangle.h> with old binutils

#include "ompt_tool_addr2line.h"

typedef struct {
   resolved_codeptr_t *resolved_codeptr;
   asymbol **image_symbols;
   bfd_vma start_addr;
   bfd_vma end_addr;
   int found;
   int so_mode;
} bfd_codeptr_data_t;

static void open_bfd_image (map_t *map)
{
   map->bfd_image = bfd_openr (map->name, 0);
   if (map->bfd_image == NULL) return;

   if (bfd_check_format (map->bfd_image, bfd_object) == 0 ||
       (bfd_get_file_flags (map->bfd_image) & HAS_SYMS) == 0)
      goto exit_open_bfd_image;

   size_t size = bfd_get_symtab_upper_bound (map->bfd_image);
   if (size == 0) goto exit_open_bfd_image;

   map->bfd_image_symbols = malloc (size);
   assert (map->bfd_image_symbols != NULL);
   size = bfd_canonicalize_symtab (map->bfd_image, map->bfd_image_symbols);
   if (size < 1) {
      free (map->bfd_image_symbols);
      map->bfd_image_symbols = NULL;
      goto exit_open_bfd_image;
   }

   return;

 exit_open_bfd_image:
   bfd_close (map->bfd_image);
   map->bfd_image = NULL;
}

static void insert_map (ompt_tool_addr2line_context_t *a2l_ctxt,
                        const void *start, const void *end,
                        unsigned long offset, const char *name)
{
   map_t *map = a2l_ctxt->maps + a2l_ctxt->nb_maps;

   map->start  = start;
   map->end    = end;
   map->offset = offset;
   map->name   = strdup (name);

   map->bfd_image = NULL;
   map->bfd_image_symbols = NULL;
   open_bfd_image (map);

   a2l_ctxt->nb_maps += 1;
}

static void load_maps (ompt_tool_addr2line_context_t *a2l_ctxt)
{
   // Open maps file
   FILE *fp = fopen ("/proc/self/maps", "r");
   if (!fp) {
      fprintf (stderr, "OMPT: Cannot open /proc/self/maps in read-only mode\n");
      return;
   }

   char buf[1024]; char *line;

   unsigned nb_maps = 0;
   // For each line in the maps file: count nb maps
   while ((line = fgets (buf, sizeof buf, fp)) != NULL)
      nb_maps++;
   rewind (fp);
   a2l_ctxt->maps = malloc (nb_maps * sizeof a2l_ctxt->maps[0]);

   // For each line in the maps file: parse maps
   while ((line = fgets (buf, sizeof buf, fp)) != NULL) {
      // Parse maps line: addr perms offset dev inode name
      const char *const delim = " ";
      const char *const addr  = strtok (line, delim);
      const char *const perms = strtok (NULL, delim);
      if (strchr (perms, 'x') == NULL) continue; // Ignore non executable maps

      const char *const offset = strtok (NULL, delim);
      strtok (NULL, delim); strtok (NULL, delim); // skip dev, inode
      char *const name = strtok (NULL, delim);

      // Space char in path: strtok has replaced the first one with '\0'
      if (name [strlen (name) - 1] != '\n')
         name [strlen (name)] = ' '; // repair (replace '\0' with a space character)

      // Remove final newline character (replace it with '\0')
      assert (name [strlen (name) - 1] == '\n');
      name [strlen (name) - 1] = '\0';

      if (!name || strlen (name) == 0) continue;

      // Parse start-end addresses
      char *addr_dup = strdup (addr);
      void *start = (void *) strtol (strtok (addr_dup, "-"), NULL, 16);
      void *end   = (void *) strtol (strtok (NULL    , "-"), NULL, 16);
      free (addr_dup);

      // Insert new map
      insert_map (a2l_ctxt, start, end, strtol (offset, NULL, 16), name);
   }

   fclose (fp);
}

void ompt_tool_addr2line_init (ompt_tool_addr2line_context_t *a2l_ctxt)
{
   if (a2l_ctxt == NULL) abort();

   a2l_ctxt->nb_maps = 0;
   a2l_ctxt->maps = NULL;

   load_maps (a2l_ctxt);
}

// Finds (and returns) the map related to a given address
static map_t *find_map (const ompt_tool_addr2line_context_t *a2l_ctxt, const void *addr)
{
   unsigned i;
   const map_t *const maps = a2l_ctxt->maps;
   for (i = 0; i < a2l_ctxt->nb_maps; i++) {
      if (addr >= maps[i].start && addr < maps[i].end)
         return (map_t *) &(maps[i]);
   }

   return NULL;
}

static void bfd_section_iter (bfd *image, asection *section, void *data)
{
   bfd_codeptr_data_t *bcd = data;

   if (bcd->found != 0) return;

#ifdef bfd_get_section_flags
   if ((bfd_get_section_flags (image, section) & SEC_ALLOC) == 0) return;
#else
   if ((bfd_section_flags (section) & SEC_ALLOC) == 0) return;
#endif

#ifdef bfd_get_section_vma
   bfd_vma vma = bfd_get_section_vma (image, section);
#else
   bfd_vma vma = bfd_section_vma (section);
#endif
   bfd_vma so_offset = 0;
   if (bcd->so_mode) {
      if (vma > section->filepos) so_offset = vma - section->filepos;
      vma = section->filepos;
   }
   if (bcd->start_addr < vma || (bcd->end_addr != 0 && bcd->end_addr < vma))
      return;

#ifdef bfd_get_section_size
   bfd_size_type size = bfd_get_section_size (section);
#else
   bfd_size_type size = bfd_section_size (section);
#endif
   if (bcd->start_addr >= vma + size || (bcd->end_addr != 0 && bcd->end_addr >= vma + size))
      return;

   bcd->found = bfd_find_nearest_line (image, section, bcd->image_symbols,
                                       bcd->start_addr - vma,
                                       (const char **) &(bcd->resolved_codeptr->src_file),
                                       (const char **) &(bcd->resolved_codeptr->fct_name),
                                       &(bcd->resolved_codeptr->src_line));

   if (bcd->found != 0)
      bcd->resolved_codeptr->module_offset = bcd->start_addr + so_offset;
}

void ompt_tool_addr2line_get (const ompt_tool_addr2line_context_t *a2l_ctxt,
                              const void *codeptr_ra, resolved_codeptr_t *rc)
{
   memset (rc, 0, sizeof *rc);

   map_t *map = find_map (a2l_ctxt, codeptr_ra);

   if (map != NULL && map->bfd_image) {
      rc->module_name = (char *) map->name;

      bfd_codeptr_data_t bcd;
      bcd.found = 0;
      bcd.image_symbols = map->bfd_image_symbols;
      bcd.resolved_codeptr = rc;
      bcd.start_addr = (unsigned long) codeptr_ra;
      bcd.end_addr = 0;
      bcd.so_mode = 0;

      if (strstr (map->name, ".so") != NULL) {
         bcd.start_addr -= (unsigned long) map->start;
         bcd.start_addr += map->offset;
         bcd.so_mode = 1;
      }

      bfd_map_over_sections (map->bfd_image, bfd_section_iter, &bcd);

      if (bcd.found != 0 && rc->fct_name != NULL)
         rc->fct_demangled_name = cplus_demangle (rc->fct_name, 0);
   }
}

static void close_bfd_image (map_t *map)
{
   free (map->bfd_image_symbols);
   map->bfd_image_symbols = NULL;

   if (map->bfd_image != NULL) {
      bfd_close (map->bfd_image);
      map->bfd_image = NULL;
   }
}

void ompt_tool_addr2line_destroy (ompt_tool_addr2line_context_t *a2l_ctxt)
{
   unsigned i;
   map_t *const maps = a2l_ctxt->maps;
   for (i=0; i<a2l_ctxt->nb_maps; i++) {
      free ((char *) maps[i].name); // strdup
      close_bfd_image (&(maps[i]));
   }
   free (maps);

#ifndef NDEBUG
   memset (a2l_ctxt, 0, sizeof *a2l_ctxt);
#endif
}
