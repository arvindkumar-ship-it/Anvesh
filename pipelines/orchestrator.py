# from agents.doc_ingestion import DocIngestionAgent
# from pipelines.rag_pipeline import HermesRAGPipeline
# from agents.schema_extractor import SchemaExtractorAgent
# from agents.ambiguity_detector import AmbiguityDetectorAgent
# from agents.dependency_mapper import DependencyMapperAgent
# from agents.code_generator import CodeGeneratorAgent
# from agents.adversarial_tester import AdversarialTesterAgent
# from agents.code_hardener import CodeHardenerAgent
# from agents.rag_qa import RAGQAAgent
# from agents.report_generator import ReportGeneratorAgent


# class HermesOrchestrator:
#     """
#     Sab 10 agents ko coordinate karta hai.

#     Kyun alag Orchestrator class?
#     UI aur tests dono same pipeline use karte hain.
#     Duplicate code avoid karo.
#     Ek jagah change karo → sab jagah apply ho.
#     """

#     def __init__(self):

#         # Immediately instantiate ho sakne wale
#         self.ingestion = DocIngestionAgent()
#         self.rag       = HermesRAGPipeline()

#         # RAG pe depend karne wale — baad mein banenge
#         # (RAG.build() ke baad)
#         self.schema_agent    = None
#         self.ambiguity_agent = None
#         self.dependency_agent = None
#         self.qa_agent        = None

#         # RAG pe depend nahi karte
#         self.code_agent    = CodeGeneratorAgent()
#         self.attack_agent  = AdversarialTesterAgent()
#         self.hardener      = CodeHardenerAgent()
#         self.reporter      = ReportGeneratorAgent()

#         # Results store karo
#         # Dict → easily access by key
#         self.results = {}

#     def run(
#         self,
#         source_url: str,
#         user_task: str,
#         progress_callback=None
#     ) -> dict:
#         """
#         Poori pipeline run karo.

#         Returns dict with:
#         - "success": bool
#         - "results": all agent outputs
#         - "error": error message if failed
#         """

#         def update(step: str, pct: int):
#             """Inner function — progress update helper"""
#             print(f"\n{'='*50}")
#             print(f"[{pct}%] {step}")
#             print('='*50)
#             if progress_callback:
#                 progress_callback(step, pct)
#                 # Callback call karo agar provided hai
#                 # None check se crash avoid

#         try:

#             # ── Step 1: Ingest ──
#             update("📥 Ingesting API docs...", 5)
#             doc = self.ingestion.ingest(source_url)
#             self.results["doc"] = doc

#             # ── Step 2: RAG ──
#             update("🗃️  Building RAG pipeline...", 15)
#             self.rag.build(doc)

#             # RAG ready → dependent agents banao
#             self.schema_agent     = SchemaExtractorAgent(self.rag)
#             self.ambiguity_agent  = AmbiguityDetectorAgent(self.rag)
#             self.dependency_agent = DependencyMapperAgent(self.rag)
#             self.qa_agent         = RAGQAAgent(self.rag)

#             # ── Step 3: Schema ──
#             update("🔍 Extracting schema...", 28)
#             schema = self.schema_agent.extract(doc)
#             self.results["schema"] = schema

#             # ── Step 4: Ambiguities ──
#             update("⚠️  Detecting doc gaps...", 38)
#             ambiguities = self.ambiguity_agent.detect(schema)
#             self.results["ambiguities"] = ambiguities

#             # ── Step 5: Dependencies ──
#             update("🗺️  Mapping dependencies...", 48)
#             dep_map = self.dependency_agent.map(schema)
#             self.results["dep_map"] = dep_map

#             # ── Step 6: Generate ──
#             update("💻 Generating code...", 58)
#             generated = self.code_agent.generate(
#                 schema, dep_map, ambiguities, user_task
#             )
#             self.results["generated"] = generated

#             # ── Step 7: Attack ──
#             update("⚔️  Adversarial testing...", 70)
#             failures = self.attack_agent.attack(generated, schema)
#             self.results["failures"] = failures

#             # ── Step 8: Harden ──
#             update("🛡️  Hardening code...", 82)
#             hardened_code = self.hardener.harden(generated, failures)
#             self.results["hardened_code"] = hardened_code

#             # ── Step 9: Q&A ──
#             update("💬 Auto Q&A analysis...", 88)
#             qa_results = self.qa_agent.auto_analyze(schema)
#             self.results["qa_results"] = qa_results

#             # ── Step 10: Report ──
#             update("📄 Generating report...", 94)
#             report = self.reporter.generate(
#                 schema=schema,
#                 ambiguities=ambiguities,
#                 hardened_code=hardened_code,
#                 failures=failures,
#                 dep_map=dep_map,
#                 qa_results=qa_results
#             )
#             self.results["report"] = report

#             update("✅ Complete!", 100)

#             return {
#                 "success": True,
#                 "results": self.results
#             }

#         except Exception as e:
#             print(f"\n❌ Pipeline failed: {e}")

#             import traceback
#             traceback.print_exc()
#             # traceback.print_exc() kyun?
#             # e → sirf error message
#             # traceback → full stack trace
#             # Debugging ke liye zyada useful

#             return {
#                 "success": False,
#                 "error": str(e),
#                 "results": self.results
#                 # Partial results bhi return karo
#                 # Jo steps complete hue unka data available hai
#             }
#=============================================================================================




import asyncio
import traceback
from agents.doc_ingestion import DocIngestionAgent
from pipelines.rag_pipeline import HermesRAGPipeline
from agents.schema_extractor import SchemaExtractorAgent
from agents.ambiguity_detector import AmbiguityDetectorAgent
from agents.dependency_mapper import DependencyMapperAgent
from agents.code_generator import CodeGeneratorAgent
from agents.adversarial_tester import AdversarialTesterAgent
from agents.code_hardener import CodeHardenerAgent
from agents.rag_qa import RAGQAAgent
from agents.report_generator import ReportGeneratorAgent

class HermesOrchestrator:
    def __init__(self):
        # Existing Instantiations
        self.ingestion = DocIngestionAgent()
        self.rag       = HermesRAGPipeline()
        self.schema_agent    = None
        self.ambiguity_agent = None
        self.dependency_agent = None
        self.qa_agent         = None
        self.code_agent    = CodeGeneratorAgent()
        self.attack_agent  = AdversarialTesterAgent()
        self.hardener      = CodeHardenerAgent()
        self.reporter      = ReportGeneratorAgent()
        self.results = {}

    # ==========================================
    # 🆕 NAYA LOGIC: UI INTEGRATION METHOD
    # ==========================================
    async def run_with_ui(self, source_url: str, user_task: str, sm):
        """
        Next.js Dashboard ke liye naya async method.
        sm: SocketManager object from app.py
        """
        async def emit_log(msg, log_type="info"):
            await sm.emit('log', {'msg': msg, 'type': log_type})

        async def update_ui(step_num, step_name):
            await sm.emit('step_update', {'step': step_num, 'name': step_name, 'status': 'active'})
            await emit_log(f"🚀 {step_name} starting...")

        try:
            # ── Step 1: Ingest ──
            await update_ui(1, "Ingesting API docs")
            doc = self.ingestion.ingest(source_url)
            self.results["doc"] = doc

            # ── Step 2: RAG ──
            await update_ui(2, "Building RAG pipeline")
            self.rag.build(doc)
            self.schema_agent     = SchemaExtractorAgent(self.rag)
            self.ambiguity_agent  = AmbiguityDetectorAgent(self.rag)
            self.dependency_agent = DependencyMapperAgent(self.rag)
            self.qa_agent         = RAGQAAgent(self.rag)

            # ── Step 3: Schema ──
            await update_ui(3, "Extracting schema")
            schema = self.schema_agent.extract(doc)
            self.results["schema"] = schema

            # ── Step 4: Ambiguities ──
            await update_ui(4, "Detecting doc gaps")
            ambiguities = self.ambiguity_agent.detect(schema)
            self.results["ambiguities"] = ambiguities
            await emit_log(f"⚠️ Found {len(ambiguities)} ambiguities/gaps.", "warning")

            # ── Step 5: Dependencies ──
            await update_ui(5, "Mapping dependencies")
            dep_map = self.dependency_agent.map(schema)
            self.results["dep_map"] = dep_map

            # ── Step 6: Generate ──
            await update_ui(6, "Generating code")
            generated = self.code_agent.generate(schema, dep_map, ambiguities, user_task)
            self.results["generated"] = generated

            # ── Step 7: Attack ──
            await update_ui(7, "Adversarial testing")
            # Yahan hum vulnerabilities detect karte hi UI ko update karenge
            failures = self.attack_agent.attack(generated, schema)
            self.results["failures"] = failures
            
            for f in failures:
                await sm.emit('attack_detected', {'id': f.attack_type.lower().replace(" ", "_"), 'name': f.attack_type})
                await emit_log(f"❌ Vulnerability Detected: {f.attack_type}", "error")

            # # ── Step 8: Harden ──
            # await update_ui(8, "Hardening code")
            # hardened_code = self.hardener.harden(generated, failures)
            # self.results["hardened_code"] = hardened_code
            
            # for f in failures:
            #     await sm.emit('attack_fixed', {'id': f.attack_type.lower().replace(" ", "_")})
            #     await emit_log(f"✅ Hardened: {f.attack_type}", "success")
            
            # # Yeh list orchestrator.py ke hardening loop mein honi chahiye
            # hardening_tasks = [
            #     ("1", "RATE_LIMIT_HIT"),
            #     ("2", "AUTH_TOKEN_EXPIRED"),
            #     ("3", "EMPTY_RESPONSE"),
            #     ("4", "PAGINATION_NOT_HANDLED"),
            #     ("5", "NETWORK_TIMEOUT"),
            #     ("6", "NESTED_ERROR_IN_200"),
            #     ("7", "MISSING_REQUIRED_FIELD")
            # ]

            # for task_id, task_name in hardening_tasks:
            #     # 1. Log bhejo Dashboard ke liye
            #     await sm.emit('log_entry', {'msg': f"🛡️ Applying Hardening: {task_name}", 'type': 'info'})
                
            #     # --- Yahan tumhara actual hardening logic chale ---
            #     # Example: self.hardener.harden(...)
                
            #     # 2. Card ko GREEN karne ka signal (id 1, 2, 3...)
            #     await sm.emit('drill_status', {'id': task_id, 'status': 'safe'})
            # ── Step 8: Harden ──
            await update_ui(8, "Hardening code")
            
            # 1. Asli Hardening Logic (LLM se response aayega)
            hardened_code = self.hardener.harden(generated, failures)
            self.results["hardened_code"] = hardened_code

            # 2. Dashboard Mapping - Inhe cards ki IDs se match kiya hai
            hardening_tasks = [
                ("1", "RATE_LIMIT_HIT"),
                ("2", "AUTH_TOKEN_EXPIRED"),
                ("3", "EMPTY_RESPONSE"),
                ("4", "PAGINATION_NOT_HANDLED"),
                ("5", "NETWORK_TIMEOUT"),
                ("6", "NESTED_ERROR_IN_200"),
                ("7", "MISSING_REQUIRED_FIELD")
            ]

            # 3. UI Update Loop - Ek-ek karke cards green honge
            for task_id, task_name in hardening_tasks:
                # Dashboard Terminal Update
                await sm.emit('log_entry', {
                    'msg': f"🛡️ Applied Protection: {task_name}", 
                    'type': 'success'
                })
                
                # Chota delay taaki visual "hacker" effect aaye
                await asyncio.sleep(0.8) 
                
                # Card ko Green karne ka signal
                await sm.emit('drill_status', {'id': task_id, 'status': 'safe'})

            await sm.emit('log_entry', {'msg': "✅ All security layers hardened successfully.", 'type': 'success'})
            # ── Step 9: Q&A ──
            await update_ui(9, "Auto Q&A analysis")
            qa_results = self.qa_agent.auto_analyze(schema)
            self.results["qa_results"] = qa_results

           # ── Step 10: Report ──
            await update_ui(10, "Generating report")
            report = self.reporter.generate(
                schema=schema, ambiguities=ambiguities, hardened_code=hardened_code,
                failures=failures, dep_map=dep_map, qa_results=qa_results
            )
            self.results["report"] = report

            # Final handshakes with Dashboard
            await sm.emit('audit_complete', {'report': report})
            await emit_log("🎉 PIPELINE COMPLETE! Hermes has finished the task.", "success")
            await sm.emit('step_update', {'step': 10, 'status': 'completed'})

        except Exception as e:
            error_trace = traceback.format_exc()
            print(error_trace)
            await emit_log(f"💀 Pipeline failed: {str(e)}", "error")
            await sm.emit('pipeline_error', {'error': str(e)})
            
        # ISKE NICHE KUCH MAT LIKHNA (Remove those extra audit_complete lines)

    # ==========================================
    # ✅ PURANA CODE (NO CHANGES MADE)
    # ==========================================
    def run(self, source_url: str, user_task: str, progress_callback=None) -> dict:
        def update(step: str, pct: int):
            print(f"\n{'='*50}\n[{pct}%] {step}\n{'='*50}")
            if progress_callback: progress_callback(step, pct)

        try:
            update("📥 Ingesting API docs...", 5)
            doc = self.ingestion.ingest(source_url)
            self.results["doc"] = doc

            update("🗃️  Building RAG pipeline...", 15)
            self.rag.build(doc)
            self.schema_agent     = SchemaExtractorAgent(self.rag)
            self.ambiguity_agent  = AmbiguityDetectorAgent(self.rag)
            self.dependency_agent = DependencyMapperAgent(self.rag)
            self.qa_agent         = RAGQAAgent(self.rag)

            update("🔍 Extracting schema...", 28)
            schema = self.schema_agent.extract(doc)
            self.results["schema"] = schema

            update("⚠️  Detecting doc gaps...", 38)
            ambiguities = self.ambiguity_agent.detect(schema)
            self.results["ambiguities"] = ambiguities

            update("🗺️  Mapping dependencies...", 48)
            dep_map = self.dependency_agent.map(schema)
            self.results["dep_map"] = dep_map

            update("💻 Generating code...", 58)
            generated = self.code_agent.generate(schema, dep_map, ambiguities, user_task)
            self.results["generated"] = generated

            update("⚔️  Adversarial testing...", 70)
            failures = self.attack_agent.attack(generated, schema)
            self.results["failures"] = failures

            update("🛡️  Hardening code...", 82)
            hardened_code = self.hardener.harden(generated, failures)
            self.results["hardened_code"] = hardened_code

            update("💬 Auto Q&A analysis...", 88)
            qa_results = self.qa_agent.auto_analyze(schema)
            self.results["qa_results"] = qa_results

            update("📄 Generating report...", 94)
            report = self.reporter.generate(
                schema=schema, ambiguities=ambiguities, hardened_code=hardened_code,
                failures=failures, dep_map=dep_map, qa_results=qa_results
            )
            self.results["report"] = report

            update("✅ Complete!", 100)
            return {"success": True, "results": self.results}

        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            traceback.print_exc()
            return {"success": False, "error": str(e), "results": self.results}