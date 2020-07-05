import numpy as np
import copy
import matplotlib.pyplot as plt


class Chromosome:

    def __init__(self, start, end, length, *args, **kwargs):
        self._metadata = np.random.uniform(low=start, high=end, size=length)
        self.system_equation = kwargs.get('system_equation')
        self.fitness = self.fitness_process()

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        self._metadata = metadata
        self.fitness = self.fitness_process()

    def fitness_process(self):
        fitness_val = 0
        for equation_object, ind_term in self.system_equation:
            result = equation_object * self.metadata
            absolute_result = abs(ind_term - sum(result))
            fitness_val += absolute_result
        return fitness_val


class GenerationProcess:

    def __init__(self, equation_schema, start, end, length, *args, **kwargs):
        self.equation_schema = equation_schema
        self.start = start
        self.end = end
        self.length = length
        self.generation_number = kwargs.get('number_generations')
        self.percentage_crossover = kwargs.get('percentage_crossover')
        self.percentage_mutation = kwargs.get('percentage_mutation')
        self.elitism_number = kwargs.get('elitism_number')
        self.generation = None

    def generate_generation(self, descendants=None):
        self.generation = [Chromosome(self.start,
                                      self.end,
                                      self.length,
                                      system_equation=self.generate_numpy_object_equation())
                           for _ in range(self.generation_number)]
        return self.generation

    def generate_numpy_object_equation(self):
        new_schema = []
        for schema in self.equation_schema:
            individual_equation = copy.copy(schema)
            independent_term = individual_equation.pop('ind_term')
            new_schema.append((np.array(list(individual_equation.values())), independent_term))
        return new_schema

    def elitism(self):
        return sorted(self.generation, key=lambda val: val.fitness)[:self.elitism_number]

    def dominant_solution(self):
        return sorted(self.generation, key=lambda val: val.fitness)[0]

    def selection(self):
        # Select a random value from 0 to generation limit number
        index_random_parent_one = np.random.choice(self.generation_number - 1)
        index_random_parent_two = np.random.choice(self.generation_number - 1)

        chromosome_one = self.generation[index_random_parent_one]
        chromosome_two = self.generation[index_random_parent_two]

        # in case the first parent have a better fitness,
        # parent one is selected otherwise the parent to is selected
        if chromosome_one.fitness > chromosome_two.fitness:
            parent_one = chromosome_one
        else:
            parent_one = chromosome_two

        # The second parent is take randomly from the dataset
        index_random_parent = np.random.choice(self.generation_number - 1)
        parent_two = self.generation[index_random_parent]
        return parent_one, parent_two

    def crossover(self, parent_one, parent_two):
        # Generate random value to validate if is possible to apply the crossover operator
        can_crossover = round(np.random.uniform(low=0.0, high=1.0), 2)
        descendant_one = parent_one
        descendant_two = parent_two

        # If the percentage is less than the percentage crossover defined the operator is going to be applied
        if can_crossover < self.percentage_crossover:
            # Select a random position from chromosome to apply one point crossover.
            # The selection need to be from 1 because the operator have
            # to be apply over the element and not in the corners
            index_to_break = np.random.randint(1, self.length)

            # Generate a descendant that contains part of the genetic information from his parents
            # according with the crossover point
            descendant_one.metadata = np.concatenate(
                [parent_one.metadata[:index_to_break], parent_two.metadata[index_to_break:]])
            descendant_two.metadata = np.concatenate(
                [parent_two.metadata[:index_to_break], parent_one.metadata[index_to_break:]])

        return descendant_one, descendant_two

    def mutation(self, descendant_one, descendant_two):
        # Generate random value to validate if is possible to apply the mutation operator
        can_mutate = round(np.random.uniform(low=0.0, high=1.0), 2)

        # If the percentage is less than the percentage mutation defined the operator is going to be applied
        if can_mutate < self.percentage_mutation:
            # Select the gene that is going to be mutated
            index_to_mutate = np.random.randint(1, self.length)

            # Generate the new data that gonna mutated the gene in the descendant
            new_data = np.random.uniform(self.start, self.end)

            # A descendant is selected randomly to apply the mutation
            descendant_to_mutate = np.random.choice([descendant_one, descendant_two])
            if descendant_to_mutate == descendant_one:
                # The gene in the descendant one is mutated with the new data
                descendant_to_mutate.metadata[index_to_mutate] = new_data
                descendant_one = descendant_to_mutate
            else:
                # The gene in the descendant two is mutated with the new data
                descendant_to_mutate.metadata[index_to_mutate] = new_data
                descendant_two = descendant_to_mutate

            return descendant_one, descendant_two
        return descendant_one, descendant_two


class Equation:

    def __init__(self, start, end,
                 incognito_number,
                 equation_object,
                 number_generations,
                 percentage_crossover,
                 percentage_mutation,
                 number_elitism):

        self.generation_number = number_generations
        self.number_elitism = number_elitism
        self.incognitos = equation_object[0].keys()
        self.undefined_values = np.array([_.get('ind_term') for _ in equation_object])
        self.equation_schema = equation_object

        self.incognitos_result = {}
        self.historial_best_solutiions = []
        self.generation = GenerationProcess(equation_object,
                                            start,
                                            end,
                                            incognito_number,
                                            number_generations=number_generations,
                                            percentage_crossover=percentage_crossover,
                                            percentage_mutation=percentage_mutation,
                                            elitism_number=elitism_number)

    def solve(self):

        print("------------ Generating 1 Generation ----------------")
        self.generation.generate_generation()
        first_generation = self.generation.dominant_solution()
        print("Best local fitness {} : fitness {}".format(first_generation.metadata, first_generation.fitness))

        # Calculate the number of iteration per generation
        iterations = int((self.generation_number - self.number_elitism) / 2)

        for _ in range(2, self.generation_number + 1):
            print("------------ Generating {} Generation ----------------".format(_))

            # Get the best solution from the generation
            best_solutions = copy.deepcopy(self.generation.elitism())
            temp_generation = []

            for across in range(iterations):
                # Select the parents from the actual iterations
                parent_one, parent_two = self.generation.selection()
                # Apply the crossover operator over the selected parents
                descendant_one, descendant_two = self.generation.crossover(parent_one, parent_two)
                # Apply a mutation over the descendants generated
                descendant_one_mutated, descendant_two_mutated = self.generation.mutation(descendant_one,
                                                                                          descendant_two)

                temp_generation.extend([descendant_one_mutated, descendant_two_mutated])

            temp_generation.extend(best_solutions)
            # The best solution of the generation is saved to the future generations
            self.generation.generation = temp_generation

            dominant_solution = self.generation.dominant_solution()
            print("Best local fitness {} : fitness {}".format(dominant_solution.metadata, dominant_solution.fitness))
            self.historial_best_solutiions.append(dominant_solution.fitness)
        print("---------------------- BEST SOLUTION FOUND OVER THE ITERATIONS -------------------------------")
        dominant_solution = self.generation.dominant_solution()
        print("Best local fitness {} : fitness {}".format(dominant_solution.metadata, dominant_solution.fitness))

        print("--------------------- APPROXIMATION RESULT -----------------------------")
        equation_translated = self.generate_numpy_object_equation()
        result = equation_translated.dot(dominant_solution.metadata.transpose())
        error_result = (abs(self.undefined_values - result) / self.undefined_values) * 100

        for incognito, solution in zip(self.incognitos, dominant_solution.metadata):
            self.incognitos_result[incognito.upper()] = round(solution, 4)
            print('{} : {}'.format(incognito, solution))

        for data, solution_equation, error in zip(self.equation_schema, list(result), error_result):
            _equation = copy.copy(data)
            _equation.pop('ind_term')
            string_equation = '{}'
            for var, value in _equation.items():
                actual_val = '{}({}){}'.format('+{}'.format(round(value, 4)) if value > 0 else round(value, 4),
                                               self.incognitos_result.get(var.upper()),
                                               '{}')
                string_equation = string_equation.format(actual_val)
            print("---- EQUATION ------ Error :  {}% ------- ".format(round(error, 4)))
            string_equation = string_equation.format(' = {}'.format(round(solution_equation, 4)))

            print(string_equation)

            plt.plot(self.historial_best_solutiions)
            plt.title("Evolution")
            plt.show()

    def generate_numpy_object_equation(self):
        new_schema = []
        for schema in self.equation_schema:
            individual_equation = copy.copy(schema)
            individual_equation.pop('ind_term')
            new_schema.append(list(individual_equation.values()))
        return np.array(new_schema)


if __name__ == "__main__":
    # Define base parameters
    generation_number = 3000

    # Elitism number : This allow to select N amount of chromosomes from generation to pass the next
    elitism_number = 500

    # Limits of the possible solution
    start_solution = 0
    end_solution = 3
    number_incognitos = 4

    crossover_percentage = 0.9
    mutation_percentage = 0.3

    equation_ = [{'x': 3, 'y': 8, 'z': 2, 'ind_term': 25},
                 {'x': 1, 'y': -2, 'z': 4, 'ind_term': 12},
                 {'x': -5, 'y': 3, 'z': 11, 'ind_term': 4}]

    equation__ = [{'A': 16.98, 'P': 9, 'V': 9, 'ind_term': 138900},
                  {'A': 15.9, 'P': 8.72, 'V': 8.52, 'ind_term': 131220},
                  {'A': 14.08, 'P': 8.2, 'V': 8.76, 'ind_term': 121280}]

    equation = [{'x1': 1, 'x2': -1, 'x3': 1, 'x4': 1, 'ind_term': 4},
                {'x1': 2, 'x2': 1, 'x3': -3, 'x4': 1, 'ind_term': 4},
                {'x1': 1, 'x2': -2, 'x3': 2, 'x4': -1, 'ind_term': 3},
                {'x1': 1, 'x2': -3, 'x3': 3, 'x4': -3, 'ind_term': 2}]

    equation_problem = Equation(start_solution,
                                end_solution,
                                number_incognitos,
                                equation,
                                generation_number,
                                crossover_percentage,
                                mutation_percentage,
                                elitism_number)

    equation_problem.solve()
