# include <stdlib.h>
# include "bounding_box_data_struct.h"

int add_box(t_box **head, int x_max, int y_max, int x_min, int y_min)
{
  t_box *new_node;

  new_node = malloc(sizeof(t_box));
  if (!new_node)
    return 1;
  new_node->x_max = x_max;
  new_node->y_max = y_max;
  new_node->x_min = x_min;
  new_node->y_min = y_min;
  new_node->next = *head;
  *head = new_node;
  return 0;
}
