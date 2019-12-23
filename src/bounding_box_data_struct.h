# pragma once

typedef struct	s_box
{
  int max_x;
  int max_y;
  int min_x;
  int min_y;
  struct s_box *next;
} t_box;

int add_box(t_box **head, int min_x, int min_y, int max_x, int max_y);
t_box *merge_boxes_list(t_box *head, t_box *second_list);
