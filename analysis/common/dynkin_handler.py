from typing import Any, Dict, List, Optional, Tuple
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from model.lie_algebra import SimpleLieAlg, SemiSimpleLieAlg, DynkinType, DynkinInfo
from common.constants import EDD_JSON


def get_edd_connections() -> Dict[str, List[str]]:
    result = dict()
    for key, value in EDD_JSON.items():
        result[key] = value["connections"]
    return result


EDD_E16 = get_edd_connections()


class DynkinHandler:
    """
    Class to handle Dynkin diagram.
    """

    def __init__(self, diagram: Dict[str, List[str]]) -> None:
        self.diagram = diagram

    def identify_ade_type(
        self,
        endpoints: List[str],
        segments: List[str],
        intersections: List[str],
        cdd: Dict[str, List[str]],
    ) -> Optional[DynkinType]:
        """
        Identify the type of the Lie algebra as A or D or E.

        Args:
            endpoints (List[str]): nodes of endpoint.
            segments (List[str]): nodes of segment.
            intersections (List[str]): nodes of intersection.
            cdd (dict): a connected Dynkin diagram.

        Returns:
            DynkinType: the type of the Lie algebra("A" or "D" or "E").
        """
        if len(endpoints) == 2 and len(intersections) == 0:
            return DynkinType.A
        elif len(endpoints) == 3 and len(intersections) == 1:
            nodes_connected_to_intersection = [label for label in cdd[intersections[0]]]
            endpoints_connected_to_intersection = [
                label for label in nodes_connected_to_intersection if label in endpoints
            ]
            segments_connected_to_intersection = [
                label for label in nodes_connected_to_intersection if label in segments
            ]
            # The type is "D" if 2 or 3 of the nodes connected to the intersection are endpoints
            # The type is "E" if one of the nodes connected to the intersection is an endpoint and the others are segments
            if len(endpoints_connected_to_intersection) >= 2:
                return DynkinType.D
            elif (
                len(endpoints_connected_to_intersection) == 1
                and len(segments_connected_to_intersection) == 2
            ):
                return DynkinType.E
            else:
                print(f"The Dynkin diagram is not ADE type")
                return None
        else:
            print(f"The Dynkin diagram is not ADE type")
            return None

    def analysis_cdd(self, cdd: Dict[str, List[str]]) -> DynkinInfo:
        """
        Analysis the connected Dynkin diagram and identify the corresponding Lie algebra.

        Args:
            cdd (Dict[str, List[str]]): connected Dynkin diagram.

        Returns:
            DynkinInfo: the information of the Dynkin diagram.
        """
        if len(cdd) == 0:
            raise Exception("Empty diagram")
        endpoints = []
        segments = []
        intersections = []
        if len(cdd) == 1:
            node, connections = next(iter(cdd.items()))
            if len(connections) == 0:
                endpoints.append(node)
                return DynkinInfo(
                    type=DynkinType.A,
                    rank=1,
                    diagram=cdd,
                    endpoints=endpoints,
                    segments=segments,
                    intersections=intersections,
                )
            else:
                raise Exception("Invalid diagram")
        # Classify the nodes into endpoints, segments or intersection
        for node, connections in cdd.items():
            if len(connections) == 1:
                endpoints.append(node)
            elif len(connections) == 2:
                segments.append(node)
            elif len(connections) == 3:
                intersections.append(node)
            else:
                raise Exception("Invalid node connections included")
        # Identify the type of the Lie algebra
        type = self.identify_ade_type(
            endpoints=endpoints,
            segments=segments,
            intersections=intersections,
            cdd=cdd,
        )
        if not type:
            raise Exception("Invalid type")
        return DynkinInfo(
            type=type,
            rank=len(cdd),
            diagram=cdd,
            endpoints=endpoints,
            segments=segments,
            intersections=intersections,
        )

    def remove_nodes(
        self, diagram: Dict[str, List[str]], removed_nodes: List[str]
    ) -> Dict[str, List[str]]:
        """
        Remove some node from the diagram.
        """
        dd = {
            node: connections[:]
            for node, connections in diagram.items()
            if node not in removed_nodes
        }
        for node in dd:
            dd[node] = [conn for conn in dd[node] if conn not in removed_nodes]
        return dd

    def get_connected_diagrams(self, diagram: Dict[str, List[str]]) -> List[DynkinInfo]:
        """
        Get connected Dynkin diagrams of ADE types from the EDD by removing two nodes.

        Args:
            diagram (Dict[str, List[str]]): Dictionary to represent a Dynkin diagram.

        Returns:
            List[DynkinInfo]: List of connected Dynkin diagrams.
        """

        def extract_connected_components(
            node: str,
            connections: List[str],
            visited_nodes: List[str],
            cdd: Dict[str, List[str]],
        ):
            visited_nodes.append(node)
            cdd[node] = diagram[node]
            # Remove nodes already extracted from the connected nodes
            connections = [c for c in connections if c not in visited_nodes]
            if len(connections) == 0:
                return
            else:
                for con in connections:
                    extract_connected_components(
                        node=con,
                        connections=diagram[con],
                        visited_nodes=visited_nodes,
                        cdd=cdd,
                    )
            return

        if len(diagram) == 0:
            return []
        visited_nodes = []
        result = []
        for node, connections in diagram.items():
            cdd = dict()
            if node in visited_nodes:
                continue
            extract_connected_components(
                node=node, connections=connections, visited_nodes=visited_nodes, cdd=cdd
            )
            result.append(self.analysis_cdd(cdd))
        return result

    def get_semi_simple_lie_algebra(
        self, dynkin_info_list: List[DynkinInfo]
    ) -> SemiSimpleLieAlg:
        """
        Get semi-simple Lie algebra from a list of connected Dynkin diagram.
        """
        result = SemiSimpleLieAlg(A=[], D=[], E=[])
        for dynkin_info in dynkin_info_list:
            if dynkin_info.type == DynkinType.A:
                result.A.append(dynkin_info.rank)
            elif dynkin_info.type == DynkinType.D:
                result.D.append(dynkin_info.rank)
            elif dynkin_info.type == DynkinType.E:
                result.E.append(dynkin_info.rank)
        return result

    def get_semi_simple_lie_algebra_from_diagram(
        self, diagram: Dict[str, List[str]]
    ) -> SemiSimpleLieAlg:
        """
        Get semi-simple Lie algebra from Dynkin diagram.
        """
        dynkin_info_list = self.get_connected_diagrams(diagram)
        return self.get_semi_simple_lie_algebra(dynkin_info_list)

    def get_kac_labels(self, dynkin_info: DynkinInfo) -> Dict[str, int]:
        """
        Get Kac labels of the connected Dynkin diagram.

        Args:
            dynkin_info (DynkinInfo): information of a Dynkin diagram.
        Returns:
            Dict[str, int]: Kac label for each node.
        """

        def set_kac_labels_to_segment(
            kac_labels: dict,
            node: str,
            previous_kac_label: int,
            previous_node: str,
        ) -> None:
            """
            Set Kac labels to segment nodes.

            Args:
                kac_labels (dict): Kac labels.
                node (str): node of which the Kac label is set.
                previous_kac_label (int): Kac label of a node located at the previous position of the node.
                previous_node (str): node located at the previous position of the node.
            """
            kac_label = previous_kac_label - 1
            kac_labels[node] = kac_label
            next_nodes = [n for n in diagram[node] if n != previous_node]
            if len(next_nodes) > 0:
                set_kac_labels_to_segment(
                    kac_labels=kac_labels,
                    node=next_nodes[0],
                    previous_kac_label=kac_label,
                    previous_node=node,
                )

        kac_labels = dict()
        dynkin_type = dynkin_info.type
        diagram = dynkin_info.diagram
        if not dynkin_info.diagram:
            return dict()
        if dynkin_type == DynkinType.A:
            for node in diagram.keys():
                kac_labels[node] = 1
        elif dynkin_type == DynkinType.D:
            for node in diagram.keys():
                if node in dynkin_info.endpoints:
                    kac_labels[node] = 1
                else:
                    kac_labels[node] = 2
        elif dynkin_type == DynkinType.E and dynkin_info.rank == 6:
            intersection_node = dynkin_info.intersections[0]
            nodes_connected_to_intersection = [n for n in diagram[intersection_node]]
            kac_labels[intersection_node] = 3
            for node in nodes_connected_to_intersection:
                set_kac_labels_to_segment(
                    kac_labels=kac_labels,
                    node=node,
                    previous_kac_label=3,
                    previous_node=intersection_node,
                )
        elif dynkin_type == DynkinType.E and dynkin_info.rank == 7:
            intersection_node = dynkin_info.intersections[0]
            nodes_connected_to_intersection = [nl for nl in diagram[intersection_node]]
            kac_labels[intersection_node] = 4
            for node in nodes_connected_to_intersection:
                if node in dynkin_info.endpoints:
                    kac_labels[node] = 2
                else:
                    set_kac_labels_to_segment(
                        kac_labels=kac_labels,
                        node=node,
                        previous_kac_label=4,
                        previous_node=intersection_node,
                    )
        elif dynkin_type == DynkinType.E and dynkin_info.rank == 8:
            intersection_node = dynkin_info.intersections[0]
            nodes_connected_to_intersection = [nl for nl in diagram[intersection_node]]
            kac_labels[intersection_node] = 6
            for node in nodes_connected_to_intersection:
                if node in dynkin_info.endpoints:
                    kac_labels[node] = 3
                else:
                    connections = [n for n in diagram[node]]
                    endpoint_connections = [
                        c for c in connections if c in dynkin_info.endpoints
                    ]
                    if len(endpoint_connections) > 0:
                        kac_labels[node] = 4
                        kac_labels[endpoint_connections[0]] = 2
                    else:
                        set_kac_labels_to_segment(
                            kac_labels=kac_labels,
                            node=node,
                            previous_kac_label=6,
                            previous_node=intersection_node,
                        )
        return kac_labels

    def add_one_extra_node(
        self,
        dynkin_info: DynkinInfo,
        kac_labels: Dict[str, int],
        extra_node: str = "-1",
    ) -> Tuple[DynkinInfo, Dict[str, int]]:
        """
        Add an extra node to the connected Dynkin diagram.

        Args:
            dynkin_info (DynkinInfo): information of the connected Dynkin diagram.
            kac_labels (Dict[str, int]): Kac labels,
            extra_node (str): extra node (default "-1").

        Returns:
            DynkinInfo: information of the extended Dynkin diagram.
            Dict[str, int]: Kac labels of the extended Dynkin diagram.
        """
        new_kac_labels = dict()
        if kac_labels:
            new_kac_labels = kac_labels
            new_kac_labels[extra_node] = 1
        dynkin_type = dynkin_info.type
        rank = dynkin_info.rank
        diagram = dynkin_info.diagram
        print(f"lie_alg: {dynkin_type}_{rank}")
        if dynkin_type == DynkinType.A:
            diagram[extra_node] = dynkin_info.endpoints
            for ep in dynkin_info.endpoints:
                diagram[ep].append(extra_node)
            dynkin_info = DynkinInfo(
                type=dynkin_type,
                rank=rank + 1,
                diagram=diagram,
                endpoints=[],
                intersections=[],
                segments=list(diagram.keys()),
            )
        elif dynkin_type == DynkinType.D:
            intersection = dynkin_info.intersections[0]
            if dynkin_info.rank == 4:
                node_connected_to_extra_node = intersection
            else:
                for ep in dynkin_info.endpoints:
                    node_connected_to_ep = diagram[ep][0]
                    if node_connected_to_ep == intersection:
                        continue
                    node_connected_to_extra_node = node_connected_to_ep
                    break
            diagram[extra_node] = [node_connected_to_extra_node]
            diagram[node_connected_to_extra_node].append(extra_node)
            endpoints = dynkin_info.endpoints + [extra_node]
            intersections = dynkin_info.intersections
            segments = dynkin_info.segments
            if rank != 4:
                segments.remove(node_connected_to_extra_node)
                intersections.append(node_connected_to_extra_node)
            dynkin_info = DynkinInfo(
                type=dynkin_type,
                rank=rank + 1,
                diagram=diagram,
                endpoints=endpoints,
                intersections=intersections,
                segments=segments,
            )
        elif dynkin_type == DynkinType.E:
            intersection = dynkin_info.intersections[0]
            node_connected_to_extra_node = ""
            for ep in dynkin_info.endpoints:
                node_connected_to_ep = diagram[ep][0]
                if rank == 6 and node_connected_to_ep == intersection:
                    node_connected_to_extra_node = ep
                    break
                if node_connected_to_ep not in dynkin_info.segments:
                    continue
                next_connected_node = [
                    n for n in diagram[node_connected_to_ep] if n != ep
                ][0]
                if rank == 7 and next_connected_node == intersection:
                    node_connected_to_extra_node = ep
                    break
                elif rank == 8 and next_connected_node in dynkin_info.segments:
                    node_connected_to_extra_node = ep
                    break
            diagram[extra_node] = [node_connected_to_extra_node]
            diagram[node_connected_to_extra_node].append(extra_node)
            dynkin_info = DynkinInfo(
                type=dynkin_type,
                rank=rank + 1,
                diagram=diagram,
                endpoints=dynkin_info.endpoints + [extra_node],
                intersections=[
                    n
                    for n in dynkin_info.intersections
                    if n != node_connected_to_extra_node
                ],
                segments=dynkin_info.endpoints + [node_connected_to_extra_node],
            )
        return dynkin_info, new_kac_labels

    def count_nonzero_roots(self, algebra: SemiSimpleLieAlg) -> int:
        """
        Count the number of non-zero roots of ADE algebra.

        Args:
            algebra (SemiSimpleLieAlg): a semi simple ADE algebra.

        Return:
            int: the number of nonzero roots of the ADE algebra
        """
        num = 0
        if len(algebra.A) != 0:
            for n in algebra.A:
                num += n * (n + 1)
        if len(algebra.D) != 0:
            for n in algebra.D:
                num += 2 * n * (n - 1)
        if len(algebra.E) != 0:
            for n in algebra.E:
                if n == 6:
                    num += 72
                elif n == 7:
                    num += 126
                elif n == 8:
                    num += 240
        return num


DH_E16: DynkinHandler = DynkinHandler(diagram=EDD_E16)
