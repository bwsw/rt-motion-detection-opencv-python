# define PY_SSIZE_T_CLEAN
# include <Python.h>
# include "maths_macros.h"
# include "bounding_box_data_struct.h"

#if PY_MAJOR_VERSION >= 3
  #define PyInt_FromLong               PyLong_FromLong
  #define PyInt_AsLong                 PyLong_AsLong
  #define PyInt_AS_LONG                PyLong_AS_LONG
#endif

PyObject *c_find_bounding_boxes(PyObject *py_rectangles)
{
  t_box *rectangles = NULL;

  // we're just converting the PyObject in a more comfortable C variant

  for (int i = PyList_Size(py_rectangles) - 1 ; i >= 0 ; --i) {
    PyObject *rect = PyList_GetItem(py_rectangles, i);
    if (add_box(&rectangles, PyInt_AsLong(PyTuple_GetItem(rect, 0)),
                                PyInt_AsLong(PyTuple_GetItem(rect, 1)),
                                PyInt_AsLong(PyTuple_GetItem(rect, 2)),
                                PyInt_AsLong(PyTuple_GetItem(rect, 3))))
      return PyErr_NoMemory();
  }

  // we add a fake head to simplify iteration through list
  if (add_box(&rectangles, 0, 0, 0, 0))
    return PyErr_NoMemory();

  // contains the rectangles we want to test. At the beginning, we want everything ofc
  t_box *test_stack = rectangles;

  while (test_stack && rectangles->next->next) {
    // contains the new computed rectangles
    t_box *new_stack = NULL;

    t_box *parent_test_rect = test_stack;
    for (t_box *test_rect = test_stack->next ; test_rect ;
	 parent_test_rect = test_rect, test_rect = test_rect->next) {

      t_box *parent_rect = rectangles;
      for (t_box *rect = rectangles->next ; rect ; parent_rect = rect, rect = rect->next) {
	if (rect == test_rect)
	  continue;
	if (MAX(rect->min_x, test_rect->min_x) < MIN(rect->max_x, test_rect->max_x) &&
	    MAX(rect->min_y, test_rect->min_y) < MIN(rect->max_y, test_rect->max_y)) {
	  if (add_box(&new_stack, MIN(rect->min_x, test_rect->min_x),
		      MIN(rect->min_y, test_rect->min_y),
		      MAX(rect->max_x, test_rect->max_x),
		      MAX(rect->max_y, test_rect->max_y)))
	    return PyErr_NoMemory();

	  // those tests allow to avoid problems due to linked-list overlap
	  if (parent_rect == test_rect) {
	    parent_rect = parent_test_rect;
	    parent_rect->next = rect->next;
	  } else if (parent_test_rect == rect) {
	    parent_test_rect = parent_rect;
	    parent_test_rect->next = test_rect->next;
	  } else {
	    parent_rect->next = rect->next;
	    parent_test_rect->next = test_rect->next;
	  }
	  if (rect == test_stack) {
	    test_stack = parent_rect;
	  }
	  free(rect);
	  free(test_rect);
	  rect = parent_rect;
	  test_rect = parent_test_rect;
	  if (test_rect == test_stack)
	    test_rect = test_rect->next;
	  break;
	}
      }

      if (!test_rect)
    	break;
    }
    // to avoid useless memory copy, we use the same buffer for "rectangles" and "test_stack"
    test_stack = merge_boxes_list(rectangles, new_stack);
  }

  py_rectangles = PyList_New(0);
  for (t_box *rect = rectangles->next ; rect ; rect = rectangles->next) {
    PyList_Append(py_rectangles, Py_BuildValue("(iiii)", rect->min_x, rect->min_y,
					   rect->max_x, rect->max_y));
    rectangles->next = rect->next;
    free(rect);
  }
  free(rectangles);

  return py_rectangles;
}
