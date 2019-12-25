# include <stdlib.h>
# include "bounding_box_data_struct.h"

int add_box(t_box **head, int min_x, int min_y, int max_x, int max_y)
{
  t_box *new_node;

  new_node = malloc(sizeof(t_box));
  if (!new_node)
    return 1;
  new_node->max_x = max_x;
  new_node->max_y = max_y;
  new_node->min_x = min_x;
  new_node->min_y = min_y;
  new_node->next = *head;
  *head = new_node;
  return 0;
}

t_box *merge_boxes_list(t_box *head, t_box *second_list)
{
  if (!second_list || !head)
    return NULL;
  for (; head->next ; head = head->next);
  head->next = second_list;
  return head;
}
