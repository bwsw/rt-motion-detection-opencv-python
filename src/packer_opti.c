# define PY_SSIZE_T_CLEAN
# include <Python.h>
# include "packer_data_structs.h"

static int is_fitting(t_rect *rect, t_free_space **free_space, int *x_rect, int *y_rect)
{
  t_free_space *parent = NULL;
  for (t_free_space *free_chunk = *free_space ; free_chunk ; parent = free_chunk, free_chunk = free_chunk->next) {
    if (rect->height > free_chunk->height || rect->width > free_chunk->width)
      continue;
    *x_rect = free_chunk->x;
    *y_rect = free_chunk->y;
    t_free_space tmp_chunks[2];
    tmp_chunks[0].x = free_chunk->x;
    tmp_chunks[0].y = free_chunk->y + rect->height;
    tmp_chunks[0].width = free_chunk->width;
    tmp_chunks[0].height = free_chunk->height - rect->height;
    tmp_chunks[1].x = free_chunk->x + rect->width;
    tmp_chunks[1].y = free_chunk->y;
    tmp_chunks[1].width = free_chunk->width - rect->width;
    tmp_chunks[1].height = free_chunk->height;
    if (!parent)
      *free_space = free_chunk->next;
    else
      parent->next = free_chunk->next;
    free(free_chunk);
    int start = 0, end = 2;
    if (!tmp_chunks[0].width || !tmp_chunks[0].height)
      start = 1;
    if (!tmp_chunks[1].width || !tmp_chunks[1].height)
      end = 1;

    if (start - end < 0) {
      for (t_free_space *tested_chunk = *free_space ; tested_chunk ; tested_chunk = tested_chunk->next) {
	for (int i = start ; i < end ; ++i) {
	  if (tested_chunk->x < tmp_chunks[i].x && tested_chunk->x > *x_rect) {
	    tested_chunk->height = tmp_chunks[i].y - tested_chunk->y;
	    if (tested_chunk->x + tested_chunk->width > tmp_chunks[i].x) {
	      tmp_chunks[i].height += tested_chunk->height;
	      tmp_chunks[i].y = tested_chunk->y;
	    }
	    break;
	  }
	  else if (tested_chunk->y < tmp_chunks[i].y && tested_chunk->y > *y_rect) {
	    tested_chunk->width = tmp_chunks[i].x - tested_chunk->x;
	    if (tested_chunk->y + tested_chunk->height > tmp_chunks[i].y) {
	      tmp_chunks[i].width += tested_chunk->width;
	      tmp_chunks[i].x = tested_chunk->x;
	    }
	    break;
	  }
	}
      }
      if (!start)
	if (free_space_add(free_space, tmp_chunks[0].width, tmp_chunks[0].height, tmp_chunks[0].x, tmp_chunks[0].y))
	  return -1;
      if (end == 2)
	if (free_space_add(free_space, tmp_chunks[1].width, tmp_chunks[1].height, tmp_chunks[1].x, tmp_chunks[1].y))
	  return -1;
    }
    return 1;
  }
  return 0;
}

/*
**
** Take in parameters
** rects, a List of tuples (height, width, id)
** bins, a List of tuples (height, width, count)
** return the same values as packer.rect_list()
**
*/
PyObject *c_pack(PyObject *py_rects, PyObject *bins)
{
  PyObject *rect_list = PyList_New(0);

  int nb_rects = PyList_Size(py_rects);
  int nb_bins = PyList_Size(bins);

  // we transform the py_rects python List in C linked list.
  // we sort it at the same time, to improve the algorithm quality
  t_rect *c_rects = NULL;
  for (int i = 0 ; i < nb_rects ; ++i) {
    PyObject *rect_tuple = PyList_GetItem(py_rects, i);
    if (rect_ordered_add(&c_rects, PyInt_AsLong(PyTuple_GetItem(rect_tuple, 0)),
		    PyInt_AsLong(PyTuple_GetItem(rect_tuple, 1)),
		    PyTuple_GetItem(rect_tuple, 2)))
      return PyErr_NoMemory();
  }

  // to simplify the loop, we add a fake head to the linked list
  if (rect_ordered_add(&c_rects, 0, 0, NULL))
    return PyErr_NoMemory();
  int overall_bin_index = 0;
  for (int i = 0 ; i < nb_bins ; ++i) {
    PyObject *bin_tuple = PyList_GetItem(bins, i);
    int height = PyInt_AsLong(PyTuple_GetItem(bin_tuple, 0));
    int width = PyInt_AsLong(PyTuple_GetItem(bin_tuple, 1));
    int count = PyInt_AsLong(PyTuple_GetItem(bin_tuple, 2));
    for (int j = 0 ; j < count ; ++j, ++overall_bin_index) {
      t_rect *parent = c_rects;
      t_free_space *free_space = NULL;
      if (free_space_add(&free_space, width, height, 0, 0))
	return PyErr_NoMemory();
      for (t_rect *rect = c_rects->next ; rect ; parent = rect, rect = rect->next) {
	int x, y;
	int ret;
	if ((ret = is_fitting(rect, &free_space, &x, &y)) == 1) {
	  PyList_Append(rect_list, Py_BuildValue("(iiiiio)", overall_bin_index, x, y, rect->width, rect->height, rect->rid));
	  parent->next = rect->next;
	  free(rect);
	  rect = parent;
	} else if (ret == -1)
	  return PyErr_NoMemory();
      }
      free_space_release_memory(free_space);
      // the stack is empty, just break
      if (!c_rects->next)
	break;
    }
    if (!c_rects->next)
      break;
  }
  free(c_rects);
  return rect_list;
}
