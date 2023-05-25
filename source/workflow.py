from collections import OrderedDict
from source.default_config import DefaultConfig
from source.cleanup import Cleanup
from source.clustering import Clustering
from source.cmd import Cmd
from source.filtering_bf_cm import FilteringBfCm
from source.filtering_af_cm import FilteringAfCm
from source.stats_af_filtering import StatsAfFiltering
from source.connectivity_modifier_new import ConnectivityModifierNew
from source.connectivity_modifier_old import ConnectivityModifierOld
from source.stage import Stage
from source.timeit import timeit
from source.constants import *
import logging
import os

# Create a custom logger
host_logger = logging.getLogger(__name__)


class Workflow:
    def __init__(self, config):
        self.stages = OrderedDict()
        self.config = config

        # Read the default config.
        self.default_config = DefaultConfig(dict(config[DEFAULT]))
        self.cmd_obj = Cmd(self.default_config)

        stage_num = 0
        # Note: maintain the order in which the sections are parsed
        if config.has_section(CLEANUP_SECTION):
            stage_num = stage_num + 1
            self._add_stage(Cleanup, CLEANUP_SECTION, stage_num)

        if config.has_section(CLUSTERING_SECTION):
            stage_num = stage_num + 1
            self._add_stage(Clustering, CLUSTERING_SECTION, stage_num)

        if config.has_section(FILTERING_BF_CM_SECTION):
            stage_num = stage_num + 1
            self._add_stage(FilteringBfCm, FILTERING_BF_CM_SECTION, stage_num)

        if config.has_section(CONNECTIVITY_MODIFIER_SECTION):
            stage_num = stage_num + 1
            # Choose between new and old cm versions
            if self.default_config.cm_version == CM_VERSION_OLD_VAL:
                self._add_stage(
                    ConnectivityModifierOld, CONNECTIVITY_MODIFIER_SECTION,
                    stage_num
                    )
            if self.default_config.cm_version == CM_VERSION_NEW_VAL:
                self._add_stage(
                    ConnectivityModifierNew, CONNECTIVITY_MODIFIER_SECTION,
                    stage_num
                    )

        if config.has_section(FILTERING_AF_CM_SECTION):
            stage_num = stage_num + 1
            self._add_stage(FilteringAfCm, FILTERING_AF_CM_SECTION, stage_num)

        if config.has_section(STATS_AF_FILTERING):
            stage_num = stage_num + 1
            self._add_stage(StatsAfFiltering, STATS_AF_FILTERING, stage_num)

    def _add_stage(self, StageClass, section_name, stage_num):
        stage_class_obj = StageClass(
            config=self.config.items(section_name),
            default_config=self.default_config,
            stage_num=stage_num,
            prev_stages=self.stages
            )
        self.stages[section_name] = stage_class_obj

    def _get_analysis_file(self, resolution, n_iter):
        op_folder_name = "analysis"
        op_folder = os.path.join(
            self.default_config.output_dir, op_folder_name
            )
        os.makedirs(op_folder, exist_ok=True)
        op_file_name = f"{self.default_config.network_name}_{resolution}_n{n_iter}_{op_folder_name}.csv"
        op_file_name = os.path.join(op_folder, op_file_name)
        return op_file_name

    def _fetch_files_to_analyse(self):
        if not self.config.has_section(CLEANUP_SECTION):
            cleaned_input_file = self.default_config.existing_ip_dict[
                CLEANED_NW_KEY]
            Stage.files_to_analyse[CLEANED_INPUT_FILE_KEY] = cleaned_input_file

        if not self.config.has_section(CLUSTERING_SECTION) and \
                CLUSTERED_NW_FILES in self.default_config.existing_ip_dict.keys():
            clustering_input_files = self.default_config.existing_ip_dict[
                CLUSTERED_NW_FILES]
            for res in clustering_input_files:
                for n_iter in clustering_input_files[res]:
                    FilteringBfCm.files_to_analyse[RESOLUTION_KEY][res][
                        n_iter].append(clustering_input_files[res][n_iter])

        if not self.config.has_section(FILTERING_BF_CM_SECTION) and \
                CM_READY_FILES in self.default_config.existing_ip_dict.keys():
            cm_ready_input_files = self.default_config.existing_ip_dict[
                CM_READY_FILES]
            for res in cm_ready_input_files:
                for n_iter in cm_ready_input_files[res]:
                    FilteringBfCm.files_to_analyse[RESOLUTION_KEY][res][
                        n_iter].append(cm_ready_input_files[res][n_iter])

    @timeit
    def generate_analysis_report(self):
        host_logger.info("******** GENERATING ANALYSIS REPORTS ********")
        self._fetch_files_to_analyse()
        for resolution in Stage.files_to_analyse[RESOLUTION_KEY]:
            for n_iter in Stage.files_to_analyse[RESOLUTION_KEY][resolution]:
                res_files_to_analyse = Stage.files_to_analyse[RESOLUTION_KEY][
                    resolution][n_iter]
                analysis_csv_file = self._get_analysis_file(resolution, n_iter)
                cmd = ['Rscript',
                       "./scripts/analysis.R",
                       Stage.files_to_analyse[CLEANED_INPUT_FILE_KEY],
                       analysis_csv_file,
                       ]
                cmd.extend(res_files_to_analyse)
                self.cmd_obj.run(cmd)
        host_logger.info(
            "******** FINISHED GENERATING ANALYSIS REPORTS ******"
            )

    @timeit
    def start(self):
        host_logger.info("******** STARTED CM WORKFLOW ********")
        for stage in self.stages.values():
            stage.execute()
        # Todo:
        list(self.stages.values())[-1].cmd_obj.write_placeholder()
        host_logger.info("******** FINISHED CM WORKFLOW ********")

    def generate_execution_time_report(self):
        import csv
        from source.timeit import execution_info, STAGE_KEY, TIME_TAKEN_KEY
        with open(
                self.default_config.execution_info_csv, 'w', newline=''
                ) as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([STAGE_KEY, TIME_TAKEN_KEY])
            for i in range(len(execution_info[STAGE_KEY])):
                writer.writerow(
                    [execution_info[STAGE_KEY][i],
                     execution_info[TIME_TAKEN_KEY][i]]
                    )
        csvfile.close()
