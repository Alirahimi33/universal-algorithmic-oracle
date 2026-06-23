"""Full pipeline orchestration with all engines."""
import time
import logging
from ..entropy.encoder import EntropyEncoder
from ..symbolic.registry import list_systems
from ..genome.chromosome import Chromosome
from ..evolution.deap_engine import EvolutionaryEngine
from ..evolution.gp_engine import GPEngine
from ..evolution.nsga_engine import NSGAEngine
from ..evaluation.fitness import FitnessEvaluator
from ..memory.archive import EvolutionaryMemory
from ..memory.mutation_bank import MutationBank
from ..memory.experiment_ledger import ExperimentLedger
from ..output.oracle_output import OracleOutputBuilder, OracleOutput

logger = logging.getLogger(__name__)


class FullPipeline:
    """Full pipeline orchestration with GA, GP, and NSGA engines.
    
    This class provides a simplified interface for running oracle predictions
    with multiple evolution strategies and comparing their results.
    """

    def __init__(self, config: dict = None):
        """Initialize the full pipeline.
        
        Args:
            config: Optional configuration dictionary with memory_path and evolution settings.
        """
        self.config = config or {}
        self.encoder = EntropyEncoder()
        self.memory = EvolutionaryMemory(self.config.get("memory_path", "data/oracle_memory.db"))
        self.mutation_bank = MutationBank(self.config.get("memory_path", "data/oracle_memory.db"))
        self.experiment_ledger = ExperimentLedger(self.config.get("memory_path", "data/oracle_memory.db"))
        self.output_builder = OracleOutputBuilder()
        self.ga_engine = EvolutionaryEngine(self.config.get("evolution", {}))
        self.gp_engine = GPEngine(self.config.get("evolution", {}))
        self.nsga_engine = NSGAEngine(self.config.get("evolution", {}))

    def run_full_cycle(self, question: str, generations: int = 50, engine: str = "ga") -> OracleOutput:
        """Run a complete evolution cycle with all engines and compare results.
        
        Args:
            question: The question to analyze.
            generations: Number of generations to evolve.
            engine: Primary engine to use ('ga', 'gp', or 'nsga').
            
        Returns:
            OracleOutput with the best result from all engines.
        """
        entropy_packet = self.encoder.encode(question)
        ep_dict = {
            "raw_question": entropy_packet.raw_question,
            "normalized_text": entropy_packet.normalized_text,
            "timestamp": entropy_packet.timestamp,
            "seed": entropy_packet.seed,
            "sha_stream": entropy_packet.sha_stream,
            "bit_stream": entropy_packet.bit_stream,
            "numeric_vector": entropy_packet.numeric_vector,
            "symbolic_tokens": entropy_packet.symbolic_tokens,
            "calendar_context": entropy_packet.calendar_context,
            "question_signature": entropy_packet.question_signature,
        }

        results = {}
        for eng_name in ["ga", "gp", "nsga"]:
            start = time.time()
            try:
                if eng_name == "gp":
                    self.gp_engine.initialize_population()
                    evolved = self.gp_engine.evolve(ep_dict, generations=generations)
                elif eng_name == "nsga":
                    evolved = self.nsga_engine.evolve(ep_dict, generations=generations)
                else:
                    if not self.ga_engine.population:
                        self.ga_engine.initialize_population()
                    evolved = self.ga_engine.evolve(ep_dict, generations=generations)

                elapsed = time.time() - start
                best = evolved[0] if evolved else None
                if best:
                    execution_result = best.execute(ep_dict)
                    results[eng_name] = {"result": execution_result, "time": elapsed, "individual": best}
            except Exception as e:
                logger.warning("Engine %s failed: %s", eng_name, e)

        if not results:
            return OracleOutput(answer="All engines failed.", disclaimer=self.output_builder.DISCLAIMER)

        best_engine = max(results.keys(), key=lambda k: results[k]["result"].get("oracle_confidence", 0))
        best_data = results[best_engine]

        return self.output_builder.build(
            best_data["individual"], best_data["result"], ep_dict,
        )

    def compare_engines(self, question: str, generations: int = 30) -> dict:
        """Compare all engines on the same question.
        
        Args:
            question: The question to analyze.
            generations: Number of generations to evolve.
            
        Returns:
            Dictionary with comparison results for each engine.
        """
        entropy_packet = self.encoder.encode(question)
        ep_dict = {
            "raw_question": entropy_packet.raw_question,
            "normalized_text": entropy_packet.normalized_text,
            "timestamp": entropy_packet.timestamp,
            "seed": entropy_packet.seed,
            "sha_stream": entropy_packet.sha_stream,
            "bit_stream": entropy_packet.bit_stream,
            "numeric_vector": entropy_packet.numeric_vector,
            "symbolic_tokens": entropy_packet.symbolic_tokens,
            "calendar_context": entropy_packet.calendar_context,
            "question_signature": entropy_packet.question_signature,
        }

        comparison = {}
        for eng_name in ["ga", "gp", "nsga"]:
            start = time.time()
            try:
                if eng_name == "gp":
                    self.gp_engine.initialize_population()
                    evolved = self.gp_engine.evolve(ep_dict, generations=generations)
                elif eng_name == "nsga":
                    evolved = self.nsga_engine.evolve(ep_dict, generations=generations)
                else:
                    if not self.ga_engine.population:
                        self.ga_engine.initialize_population()
                    evolved = self.ga_engine.evolve(ep_dict, generations=generations)

                elapsed = time.time() - start
                best = evolved[0] if evolved else None
                if best:
                    exec_result = best.execute(ep_dict)
                    comparison[eng_name] = {
                        "confidence": exec_result.get("oracle_confidence", 0),
                        "time": elapsed,
                        "generations": generations,
                        "systems_used": len(set(g.system_id for g in (best.genes.values() if isinstance(best.genes, dict) else best.genes))),
                    }
            except Exception as e:
                logger.warning("Engine %s failed: %s", eng_name, e)
                comparison[eng_name] = {"error": str(e), "time": time.time() - start}

        return comparison
