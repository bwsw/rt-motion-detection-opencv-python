# pragma once

# define PY_SSIZE_T_CLEAN
# include <Python.h>

// represent a rectangle
typedef struct s_rect
{
  int height;
  int width;
  int area;
  PyObject *rid;
  struct s_rect *next;
} t_rect;

int rect_ordered_add(t_rect **head, int height, int width, PyObject *rid);

// represent a chunk of free space in a bin
// x & y are the coordinate of the top left corner
typedef struct	s_free_space
{
  int width;
  int height;
  int x;
  int y;
  struct s_free_space *next;
} t_free_space;

int free_space_add(t_free_space **head, int width, int height, int x, int y);
void free_space_release_memory(t_free_space *head);
