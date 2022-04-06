# pragma once

typedef struct s_coord_list
{
  struct s_coord_list *next;
  int r;
  int c;
} t_c_list;

int add_coord(t_c_list **head, int r, int c);
