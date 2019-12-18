# define PY_SSIZE_T_CLEAN
# include <Python.h>
# include "coord_list.h"
# include <string.h>

# define MAX(x, y) (x > y ? (x) : (y))
# define MIN(x, y) (x < y ? (x) : (y))

# define ABS(x) (x < 0 ? (-(x)) : (x))

PyObject *c_scan(PyObject *image, int expansion_step)
{
  /*
  **
  ** on this block we set up all the needed values
  ** (see Scanner.__init__())
  **
  */

  PyObject *boxes = PyList_New(0);
  int height = PyInt_AsLong(PyTuple_GetItem(PyObject_GetAttrString(image, "shape"), 0));
  int width = PyInt_AsLong(PyTuple_GetItem(PyObject_GetAttrString(image, "shape"), 1));
  t_c_list *scan_points = NULL;
  char **avoid_points = malloc(height * sizeof(char*));
  if (!avoid_points)
    return PyErr_NoMemory();

  // this double loop init both avoid_points and scan_points
  for (int r = 0 ; r < height ; ++r) {
    PyObject *row = PyList_GetItem(image, r);
    avoid_points[r] = malloc(width * sizeof(char));
    if (!avoid_points[r])
      return PyErr_NoMemory();
    memset(avoid_points[r], 1, width * sizeof(char));

    for (int c = 0 ; c < width ; ++c) {
      if (0 < PyInt_AsLong(PyList_GetItem(row, c))) {
	if (add_coord(&scan_points, r, c))
	  return PyErr_NoMemory();
	avoid_points[r][c] = 0;
      }
    }
  }

  /*
  **
  ** here is the beggining of the algorithm
  ** (see Scanner.scan())
  **
  */

  for (t_c_list *coord = scan_points ; coord ; coord = scan_points) {
    scan_points = coord->next;

    if (!avoid_points[coord->r][coord->c]) {
      /*
      ** transcription of numba_scan_box()
      */

      int r_min = 0;
      int c_min = 0;
      int r_max = height;
      int c_max = width;
      t_c_list *nl = NULL;
      if (add_coord(&nl, coord->r, coord->c))
	return PyErr_NoMemory();
      for (t_c_list *nl_coord = nl ; nl_coord ; nl_coord = nl) {
	nl = nl_coord->next;

	r_min = MIN(r_min, nl_coord->r);
	c_min = MIN(c_min, nl_coord->c);
	r_max = MAX(r_max, nl_coord->r);
	c_max = MAX(c_max, nl_coord->c);

	/*
	** transcription of numba_get_neighbors()
	*/
	for (int i = -expansion_step ; i < expansion_step + 1 ; ++i) {
	  for (int j = -expansion_step ; j < expansion_step + 1 ; ++j) {
	    int r = i + nl_coord->r;
	    int c = j + nl_coord->c;
	    if (r >= 0 && c >= 0 && r < height && c < width && !avoid_points[r][c]) {
	      avoid_points[r][c] = 1;
	      if (ABS(i) == expansion_step || ABS(j) == expansion_step) {
		if (add_coord(&nl, r, c))
		  return PyErr_NoMemory();
	      }
	    }
	  }
	}
	/*
	** end of transcription of numba_get_neighbors()
	*/

	free(nl_coord);
      }

      r_min = MIN(0, r_min - expansion_step);
      c_min = MIN(0, c_min - expansion_step);

      r_max = MAX(height - 1, r_max + expansion_step);
      c_max = MAX(width - 1, c_max + expansion_step);

      PyList_Append(boxes, PyTuple_Pack(4, PyInt_FromLong(c_min), PyInt_FromLong(r_min), PyInt_FromLong(c_max), PyInt_FromLong(r_max)));

      /*
      ** end of transcription of numba_scan_box()
      */
    }
    free(coord);
  }

  for (int r = 0 ; r < height ; ++r)
    free(avoid_points[r]);
  free(avoid_points);
  return boxes;
}
