import math
import png
import shutil
import struct

from benchmark import *
from benchmark_middlebury2014 import *
from util import *


class Kitti2015(Benchmark):
    def Name(self):
        return "Kitti 2015 Stereo"
    
    
    def Prefix(self):
        return "Kitti2015_"
    
    
    def Website(self):
        return 'http://www.cvlibs.net/datasets/kitti/eval_scene_flow.php?benchmark=stereo'
    
    
    def SupportsTrainingDataOnlySubmissions(self):
        return False
    
    
    def SupportsTrainingDataInFullSubmissions(self):
        return False
    
    
    def GetOptions(self):
        return  # No options
    
    
    def DownloadAndConvert(self, archive_dir_path, unpack_dir_path, datasets_dir_path, training_dir_path, test_dir_path):
        # Download input images (training + test) and ground truth
        DownloadAndUnzipFile('http://kitti.is.tue.mpg.de/kitti/data_scene_flow.zip', archive_dir_path, unpack_dir_path)
        
        # NOTE: Calibration files would be here:
        # http://kitti.is.tue.mpg.de/kitti/data_scene_flow_calib.zip
        
        # NOTE: Multi-view extension would be here:
        # http://kitti.is.tue.mpg.de/kitti/data_scene_flow_multiview.zip
        
        self.ConvertOriginalToMiddlebury(unpack_dir_path, training_dir_path, test_dir_path)
    
    
    def ConvertOriginalToMiddlebury(self, unpack_dir_path, training_dir_path, test_dir_path):
        src_training_path = os.path.join(unpack_dir_path, 'training')
        src_testing_path = os.path.join(unpack_dir_path, 'testing')
        
        for folder_names in [(src_testing_path, test_dir_path),
                             (src_training_path, training_dir_path)]:
            input_folder_path = folder_names[0]
            
            image_2_path = os.path.join(input_folder_path, 'image_2')  # contains left images
            image_3_path = os.path.join(input_folder_path, 'image_3')  # contains right images
            
            for image_name in os.listdir(image_2_path):
                dataset_name = image_name[:image_name.rfind('.')]  # remove file extension
                if dataset_name.endswith('_11'):
                    continue  # These files are for flow only, skip them
                
                output_dataset_path = os.path.join(folder_names[1], self.Prefix() + dataset_name)
                MakeDirsExistOk(output_dataset_path)
                
                # Move images
                shutil.move(os.path.join(image_2_path, image_name),
                            os.path.join(output_dataset_path, 'im0.png'))
                shutil.move(os.path.join(image_3_path, image_name),
                            os.path.join(output_dataset_path, 'im1.png'))
                
                # Create calib.txt
                left_fx = -1  # TODO
                left_fy = -1  # TODO
                left_cx = -1  # TODO
                left_cy = -1  # TODO
                right_fx = -1  # TODO
                right_fy = -1  # TODO
                right_cx = -1  # TODO
                right_cy = -1  # TODO
                baseline_in_mm = -1  # TODO
                
                png_reader = png.Reader(os.path.join(output_dataset_path, 'im0.png'))
                png_data = png_reader.read()
                width = png_data[0]
                height = png_data[1]
                png_reader.close()
                
                ndisp = 256  # According to Kitti's devkit README
                
                calib_path = os.path.join(output_dataset_path, 'calib.txt')
                WriteMiddlebury2014CalibFile(
                    calib_path,
                    left_fx, left_fy, left_cx, left_cy,
                    right_fx, right_fy, right_cx, right_cy,
                    baseline_in_mm,
                    width,
                    height,
                    ndisp)
                
                # For training datasets:
                if folder_names[1] == training_dir_path:
                    # Convert ground truth.
                    disp_noc_0_reader = png.Reader(os.path.join(input_folder_path, 'disp_noc_0', image_name))
                    disp_noc_0_data = disp_noc_0_reader.read()
                    if disp_noc_0_data[3]['bitdepth'] != 16:
                        raise Exception('bitdepth of ' + os.path.join(input_folder_path, 'disp_noc_0', image_name) + ' is not 16')
                    
                    disp_occ_0_reader = png.Reader(os.path.join(input_folder_path, 'disp_occ_0', image_name))
                    disp_occ_0_data = disp_occ_0_reader.read()
                    if disp_occ_0_data[3]['bitdepth'] != 16:
                        raise Exception('bitdepth of ' + os.path.join(input_folder_path, 'disp_occ_0', image_name) + ' is not 16')
                    
                    # Get lists of rows for each image.
                    disp_noc_0 = list(disp_noc_0_data[2])
                    disp_occ_0 = list(disp_occ_0_data[2])
                    
                    # Convert the 'occ' file to Middlebury's PFM format.
                    disp_occ_0_float = []
                    for y in range(len(disp_occ_0) - 1, -1, -1):  # iterate in reverse order according to pfm format
                        input_line = disp_occ_0[y]
                        for value in input_line:
                            if value > 0:
                                disp_occ_0_float.append(float(value) / 256.0)
                            else:
                                disp_occ_0_float.append(float('inf'))  # invalid value
                    
                    WriteMiddlebury2014PfmFile(os.path.join(output_dataset_path, 'disp0GT.pfm'), width, height, disp_occ_0_float)
                    
                    # Compute mask0nocc.png from disp_noc_0 and disp_occ_0.
                    mask0nocc = []  # list of rows
                    for y in range(0, len(disp_occ_0)):
                        disp_occ_0_line = disp_occ_0[y]
                        disp_noc_0_line = disp_noc_0[y]
                        row = []
                        for x in range(0, len(disp_occ_0_line)):
                            if disp_occ_0_line[x] == 0:
                                row.append(0)  # no ground truth for this pixel
                            elif disp_noc_0_line[x] == 0:
                                row.append(128)  # occluded pixel
                            else:
                                row.append(255)  # non-occluded pixel
                        mask0nocc.append(row)
                    
                    with open(os.path.join(output_dataset_path, 'mask0nocc.png'), 'wb') as mask_file:
                        mask_writer = png.Writer(width=width, height=height, bitdepth=8, compression=9, greyscale=True)
                        mask_writer.write(mask_file, mask0nocc)
                    
                    # Move additional file(s).
                    shutil.move(os.path.join(input_folder_path, 'obj_map', image_name),
                                os.path.join(output_dataset_path, 'obj_map.png'))
                    
                    disp_noc_0_reader.close()
                    disp_occ_0_reader.close()
            
            # Delete original folder
            shutil.rmtree(input_folder_path)
    
    
    def CreateSubmissionArchive(self, method, datasets_dir_path, training_dataset_names, test_dataset_names, training_dir_path, test_dir_path, pack_dir_path, archive_base_path):
        # Create output directory
        disp_0_path = os.path.join(pack_dir_path, 'disp_0')
        MakeDirsExistOk(disp_0_path)
        
        # Only test dataset submission is supported.
        for benchmark_and_dataset_name in test_dataset_names:
            src_dataset_path = os.path.join(test_dir_path, benchmark_and_dataset_name)
            original_dataset_name = benchmark_and_dataset_name[len(self.Prefix()):]
            
            # Convert .pfm to Kitti's .png disparity
            src_pfm_path = os.path.join(src_dataset_path, 'disp0' + method + '.pfm')
            (pfm_width, pfm_height, pfm_pixels) = ReadMiddlebury2014PfmFile(src_pfm_path)
            
            png_disp = []  # list of rows
            for y in range(pfm_height - 1, -1, -1):  # iterate in reverse order according to pfm format
                in_row = pfm_pixels[y * pfm_width : (y + 1) * pfm_width]
                out_row = []
                for value in in_row:
                    if math.isinf(value):
                        out_row.append(0)  # invalid value
                    else:
                        out_row.append(max(1, int(round(256.0 * value))))
                png_disp.append(out_row)
            
            dest_png_path = os.path.join(disp_0_path, original_dataset_name + '.png')
            with open(dest_png_path, 'wb') as dest_png_file:
                png_writer = png.Writer(width=pfm_width, height=pfm_height, bitdepth=16, compression=9, greyscale=True)
                png_writer.write(dest_png_file, png_disp)
        
        # Create the archive and clean up.
        archive_filename = ZipDirectory(archive_base_path, pack_dir_path)
        DeleteFolderContents(pack_dir_path)
        
        return archive_filename
    