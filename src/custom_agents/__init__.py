# This file makes the agents directory a package
from .curriculum_agent import curriculum_agent
from .reviewer_agent import reviewer_agent
from .detail_agent import detail_agent
from .material_agent import material_agent

__all__ = ['curriculum_agent', 'reviewer_agent', 'detail_agent', 'material_agent']
