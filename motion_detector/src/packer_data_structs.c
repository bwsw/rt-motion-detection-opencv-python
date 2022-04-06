# include "packer_data_structs.h"
# include <stdlib.h>

int rect_ordered_add(t_rect **head, int height, int width, PyObject *rid)
{
  t_rect *new_node = malloc(sizeof(t_rect));
  if (!new_node)
    return 1;

  new_node->height = height;
  new_node->width = width;
  new_node->area = height * width;
  new_node->rid = rid;

  if (!*head || (*head)->area <= new_node->area) {
    new_node->next = *head;
    *head = new_node;
    return 0;
  }

  for (t_rect *tmp_node = *head ; tmp_node ; tmp_node = tmp_node->next) {
    if (!tmp_node->next || tmp_node->next->area <= new_node->area) {
      new_node->next = tmp_node->next;
      tmp_node->next = new_node;
      break;
    }
  }

  return 0;
}

int free_space_add(t_free_space **head, int width, int height, int x, int y)
{
  t_free_space *new_node = malloc(sizeof(t_free_space));
  if (!new_node)
    return 1;

  new_node->width = width;
  new_node->height = height;
  new_node->x = x;
  new_node->y = y;
  new_node->next = *head;
  *head = new_node;

  return 0;
}

void free_space_release_memory(t_free_space *head)
{
  if (!head)
    return;
  free_space_release_memory(head->next);
  free(head);
  return;
}
