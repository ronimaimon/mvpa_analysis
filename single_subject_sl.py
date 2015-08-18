#!/usr/bin/python

from mvpa2.suite import *
from mvpa2.cmdline.helpers import arg2ds

def do_searchlight(glm_dataset, radius, output_basename, with_null_prob=False):
	clf  = LinearCSVMC(space='condition')
#		clf = RbfCSVMC(C=5.0)
	splt = NFoldPartitioner()
	cv = CrossValidation(clf,splt, 
			     errorfx=mean_match_accuracy,
			     enable_ca=['stats'], postproc=mean_sample() )
	distr_est = []
	if with_null_prob:
		
		
		permutator = AttributePermutator('condition', count=100,
				  limit='chunks')
		distr_est = MCNullDist(permutator, tail='left',
			enable_ca=['dist_samples'])
		"""
		repeater   = Repeater(count=100)
		permutator = AttributePermutator('condition', limit={'partitions': 1}, count=1) 
		null_cv = CrossValidation(clf, ChainNode([splt, permutator],space=splt.get_space()),
					  postproc=mean_sample())
		null_sl = sphere_searchlight(null_cv, radius=radius, space='voxel_indices',
					     enable_ca=['roi_sizes'])
		distr_est = MCNullDist(repeater,tail='left', measure=null_sl,
				       enable_ca=['dist_samples'])
		"""
		sl = sphere_searchlight(cv, radius=radius, space='voxel_indices',
				null_dist=distr_est,
				enable_ca=['roi_sizes','roi_feature_ids'])
	else:

		sl = sphere_searchlight(cv, nproc=20,radius=radius, space='voxel_indices',
				enable_ca=['roi_sizes','roi_feature_ids'])
	#ds = glm_dataset.copy(deep=False,
	#		       sa=['condition','chunks'],
	#		       fa=['voxel_indices'],
	#		       a=['mapper'])
	now = datetime.datetime.now()
	print glm_dataset.shape
	print now
	debug.active += ["SLC"]
	sl_map = sl(glm_dataset)
	print datetime.datetime.now() - now
	errresults = map2nifti(sl_map,
				 imghdr=glm_dataset.a.imghdr)
	errresults.to_filename('{}-acc.nii.gz'.format(output_basename))
	sl_map.samples *= -1
	sl_map.samples += 1
	niftiresults = map2nifti(sl_map,
				 imghdr=glm_dataset.a.imghdr)
	niftiresults.to_filename('{}-err.nii.gz'.format(output_basename))
	#TODO: save p value map
	if with_null_prob:
		nullt_results = map2nifti(sl_map,data=sl.ca.null_t,
				 imghdr=glm_dataset.a.imghdr)
		nullt_results.to_filename('{}-t.nii.gz'.format(output_basename))
		nullprob_results = map2nifti(sl_map,data=sl.ca.null_prob,
				 imghdr=glm_dataset.a.imghdr)
		nullprob_results.to_filename('{}-prob.nii.gz'.format(output_basename))
		nullprob_results = map2nifti(sl_map,data=distr_est.cdf(sl_map.samples),
				 imghdr=glm_dataset.a.imghdr)
		nullprob_results.to_filename('{}-cdf.nii.gz'.format(output_basename))
		
if __name__ == '__main__':
	filename = sys.argv[1]
	radius   = sys.argv[2]
	print filename		
	output_basename = os.path.join('{}_r{}_c-{}'.format(filename, radius,'linear'))
	print output_basename
	glm_dataset = arg2ds([filename])
	do_searchlight(glm_dataset, radius, output_basename,
						False)
