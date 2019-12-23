# pragma once

typedef struct	s_box
{
  int x_max;
  int y_max;
  int x_min;
  int y_min;
  struct s_box *next;
} t_box;

int add_box(t_box **head, int x_max, int y_max, int x_min, int y_min);
