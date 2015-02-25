from IPython.nbconvert.preprocessors import Preprocessor
from IPython.utils.traitlets import Unicode
from nbgrader import utils
from nbgrader.api import Gradebook
from sqlalchemy.orm.exc import NoResultFound

class OverwriteGradeCells(Preprocessor):
    """A preprocessor to save information about grade cells."""

    db_url = Unicode("sqlite:///gradebook.db", config=True, help="URL to database")
    assignment_id = Unicode(u'assignment', config=True, help="Assignment ID")

    def preprocess(self, nb, resources):
        self.gradebook = Gradebook(self.db_url)
        self.notebook_id = resources['unique_key']

        nb, resources = super(OverwriteGradeCells, self).preprocess(nb, resources)

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        if utils.is_grade(cell):
            try:
                grade_cell = self.gradebook.find_grade_cell(
                    cell.metadata.nbgrader.grade_id,
                    self.notebook_id,
                    self.assignment_id)
            except NoResultFound:
                return cell, resources
            except:
                raise

            cell.metadata.nbgrader['points'] = grade_cell.max_score

            # we only want the source and checksum for non-solution cells
            if not utils.is_solution(cell) and grade_cell.source:
                old_checksum = grade_cell.checksum
                new_checksum = utils.compute_checksum(cell)

                if old_checksum != new_checksum:
                    self.log.warning("Checksum for grade cell %s has changed!", grade_cell.name)

                cell.source = grade_cell.source
                cell.cell_type = grade_cell.cell_type
                cell.metadata.nbgrader['checksum'] = grade_cell.checksum

            self.log.debug("Overwrote grade cell %s", grade_cell.name)

        return cell, resources
