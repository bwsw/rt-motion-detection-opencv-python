# include "coord_list.h"
# include <stdlib.h>

int add_coord(t_c_list **head, int r, int c)
{
  t_c_list *new_node;

  new_node = malloc(sizeof(t_c_list));
  if (!new_node)
    return 1;
  new_node->r = r;
  new_node->c = c;
  new_node->next = *head;
  *head = new_node;
  return 0;
}
