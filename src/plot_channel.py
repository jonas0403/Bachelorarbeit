# Author: Jonas Scholz
# Version: 23.07.2025
# Plot_channel
# Programm for plotting the entered channel contour


import math 
import numpy as np
import matplotlib.pyplot as plt
import debug_log

from cubic_spline import cubspline

Pi = math.pi

h_H = [0.0, 0.2, 0.5, 0.8, 1.0] # Temporary here and not imported

plot_mirrored = 0 # Temporary here and not in the GUI


def plot_channel(D_S1, D_S2, D_S3, D_H1, D_H2, D_H3, D_M1, D_M2, D_M3,i_st, l_R, l_S, beta_blade_1, beta_blade_2, alpha_blade_2, alpha_blade_3):
    
    # factors for space between the rows    
    Rotor = [0.4, 0.15, 0.2]
    Stator = [0.3, 0.15, 0.4]
    
    # Defines parameter spaceing for spline interpolation
    t0 = np.arange(-1.0, 8.0, 1.0) # Base parameter values for the control points
    t1 = np.arange(-1, 1.05, 0.05)
    t2 = np.arange(1.025, 2.025, 0.025)
    t3 = np.arange(2.05, 4.05, 0.05)
    t4 = np.arange(4.025, 5.025, 0.025)
    t5 = np.arange(5.05, 7.05, 0.05)
    t_interp = np.concatenate((t1, t2, t3, t4, t5)) # Interpolation parameter values
    
    
    # Initialize lists to store geometry data for each stage
    all_x0_stages = []
    all_r0_N_stages = []
    all_r0_G_stages = []
    all_x_N_stages = []
    all_r_N_stages = []
    all_x_G_stages = []
    all_r_G_stages = []
    all_channelHeight_stages = []
    all_meanline_stages = []
    all_m_prime_N_stages = []
    all_m_prime_G_stages = []
    all_x_values_stages = []
    all_r_values_stages = []
    all_m_prime_values_stages = []
    
   # Keep track of the total axial offset for multi-stage plotting
    current_axial_offset = 0.0
    
    
    # Loop through each stage to calculate its geometry
    for stage_idx in range(i_st):
        
        
        x0 = np.full_like(t0, 0.0) # Reset for each stage
        x0[1] = 0.0 # Stage relative inlet
        x0[2] = round(Rotor[0]*l_R[stage_idx], 1) 
        x0[0] = -1*round((x0[2]-x0[1])/(1-Rotor[0]), 0)
        x0[3] = x0[2] + round((1+Rotor[1]) * l_R[stage_idx] *(math.sin((beta_blade_1[stage_idx]+beta_blade_2[stage_idx])/(2*180)*Pi)),1)
        x0[4] = x0[3] + round(Rotor[2]*l_R[stage_idx],1) 
        x0[5] = x0[4] + round((Stator[0]+Stator[1]/2)*l_S[stage_idx], 1)
        x0[6] = x0[5] + round((1+Stator[1]) * l_S[stage_idx] *(math.sin((alpha_blade_2[stage_idx]+alpha_blade_3[stage_idx])/(2*180)*Pi)),1)
        x0[7] = x0[6] + round((Stator[2]+Stator[1]/2)*l_S[stage_idx], 1)
        x0[8] = x0[7] + round((x0[7]-x0[6])/(1-Stator[2]))
        
        # Add current_axial_offset to x0 points for global positioning
        x0 = [val + current_axial_offset for val in x0]
        
        # Calculate radial reference points (r0_N, r0_G) for the current stage
        
        r0_N = np.full_like(t0, 0.0)
        r0_N[1] = round(D_H1[stage_idx]/2, 1) 
        r0_N[2] = r0_N[1] + round((D_H2[stage_idx]-D_H1[stage_idx])/2*(x0[2]-x0[1])/(x0[4]-x0[1]), 1)
        r0_N[0] = round((r0_N[2]-r0_N[1])/(x0[2]-x0[1])*(x0[0]-x0[1])+r0_N[1], 1) # Adjusted for x0 offset
        r0_N[3] = r0_N[1]+ round((D_H2[stage_idx]-D_H1[stage_idx])/2*(x0[3]-x0[1])/(x0[4]-x0[1]), 1)
        r0_N[5] = round(D_H2[stage_idx]/2, 1) + round((D_H3[stage_idx]-D_H2[stage_idx])/2*(x0[5]-x0[4])/(x0[7]-x0[4]), 1)
        r0_N[4] = round((D_H2[stage_idx]/2 + (r0_N[3]+(r0_N[5]-r0_N[3])*(x0[4]-x0[3])/(x0[5]-x0[3])))/2 ,1)
        r0_N[6] = round(D_H2[stage_idx]/2, 1) + round((D_H3[stage_idx]-D_H2[stage_idx])/2*(x0[6]-x0[4])/(x0[7]-x0[4]), 1)
        r0_N[7] = round(D_H3[stage_idx]/2, 1)
        r0_N[8] = round((r0_N[7] - r0_N[6])/(x0[7] - x0[6])*(x0[8] - x0[7]) + r0_N[7], 1)
        
        
        
        r0_G = np.full_like(t0, 0.0)
        r0_G[1] = round(D_S1[stage_idx]/2, 1)
        r0_G[2] = r0_G[1] + round((D_S2[stage_idx]-D_S1[stage_idx])/2*(x0[2]-x0[1])/(x0[4]-x0[1]), 1)
        r0_G[0] = round((r0_G[2]-r0_G[1])/(x0[2]-x0[1])*(x0[0]-x0[1])+r0_G[1], 1) # Adjusted for x0 offset
        r0_G[3] = r0_G[1]+ round((D_S2[stage_idx]-D_S1[stage_idx])/2*(x0[3]-x0[1])/(x0[4]-x0[1]), 1)
        r0_G[5] = round(D_S2[stage_idx]/2, 1) + round((D_S3[stage_idx]-D_S2[stage_idx])/2*(x0[5]-x0[4])/(x0[7]-x0[4]), 1)
        r0_G[4] = round((D_S2[stage_idx]/2 + (r0_G[3]+(r0_G[5]-r0_G[3])*(x0[4]-x0[3])/(x0[5]-x0[3])))/2 ,1)
        r0_G[6] = round(D_S2[stage_idx]/2, 1) + round((D_S3[stage_idx]-D_S2[stage_idx])/2*(x0[6]-x0[4])/(x0[7]-x0[4]), 1)
        r0_G[7] = round(D_S3[stage_idx]/2, 1)
        r0_G[8] = round((r0_G[7] - r0_G[6])/(x0[7] - x0[6])*(x0[8] - x0[7]) + r0_G[7], 1)
 
        # Define the actual t_interp range for the current stage to remove inter-stage linear extrapolations
        t_current_interp = []
        if stage_idx == 0:
            # For the first stage, include the pre-inlet extrapolation range (t < 0)
            t_current_interp = t_interp
        else:
            # For subsequent stages, start from t=0 (rotor inlet) to remove the pre-inlet extrapolation
            t_current_interp = t_interp[t_interp >= 0.0]

        if stage_idx == i_st - 1:
            # For the last stage, include the post-outlet extrapolation range (t > 6)
            pass # t_current_interp is already set as needed
        else:
            # For intermediate stages, end at t=6 (stator outlet) to remove the post-outlet extrapolation
            t_current_interp = t_current_interp[t_current_interp <= 6.0]
        
        # Generate Hub and Shroud spine points
        x_N = []
        r_N = []
        x_G = []
        r_G = []
        # Recalculate slopes for linear extrapolation for radial values (these slopes are used if t_val falls in the extrapolation range)
        s1_rN = (r0_N[1]-r0_N[0])/(t0[1]-t0[0])
        s2_rN = (r0_N[8]-r0_N[7])/(t0[8]-t0[7])
        s1_rG = (r0_G[1]-r0_G[0])/(t0[1]-t0[0])
        s2_rG = (r0_G[8]-r0_G[7])/(t0[8]-t0[7])

        for t_val in t_current_interp: # Loop over the filtered t_current_interp
            s1_x = (x0[1]-x0[0])/(t0[1]-t0[0]) # slope for t < 0
            s2_x = (x0[8]-x0[7])/(t0[8]-t0[7]) # slope for t > 6

            if t_val < 0.0: # This only applies to the very first stage
                x_N.append(s1_x*t_val+x0[1])
                r_N.append(s1_rN*t_val+r0_N[1])
                x_G.append(s1_x*t_val+x0[1]) # x_G is the same as x_N
                r_G.append(s1_rG*t_val+r0_G[1])
            elif t_val >= 0 and t_val <=6:
                x_N.append(cubspline(3,t_val, t0[1:8], x0[1:8]))
                r_N.append(cubspline(3,t_val, t0[1:8], r0_N[1:8]))
                x_G.append(cubspline(3,t_val, t0[1:8], x0[1:8]))
                r_G.append(cubspline(3,t_val, t0[1:8], r0_G[1:8]))
            elif t_val > 6: # This only applies to the very last stage (and potentially first stage if i_st=1)
                x_N.append(s2_x*(t_val-t0[8]) + x0[8])
                r_N.append(s2_rN*(t_val-t0[8]) + r0_N[8])
                x_G.append(s2_x*(t_val-t0[8]) + x0[8]) # x_G is the same as x_N
                r_G.append(s2_rG*(t_val-t0[8]) + r0_G[8])

        # Store results for the current stage
        # Store x0 and r0_N/r0_G before filtering for plotting
        
        all_x_N_stages.append(x_N)
        all_r_N_stages.append(r_N)
        all_x_G_stages.append(x_G)
        all_r_G_stages.append(r_G)
        
        all_x0_stages.append(list(x0))
        all_r0_N_stages.append(list(r0_N))
        all_r0_G_stages.append(list(r0_G))
        
        # Calculate and store channel height for current stage
        channelHeight_stage = []
        # Calculate channel height based on the *interpolated* hub and shroud radii
        for i in range(len(r_G)): # Use the length of the interpolated lists
            channelHeight_stage.append(r_G[i] - r_N[i])
        all_channelHeight_stages.append(channelHeight_stage)
        
        # Calculate and store meanline for current stage
        meanline_stage = []
        for i in range(len(t_current_interp)): # Use t_current_interp for meanline
            meanline_stage.append((r_G[i]+r_N[i])/2)
        all_meanline_stages.append(meanline_stage)

        m_prime_N_final = [0.0] * len(t_current_interp)
        for i in range(len(t_current_interp)-1):
            segment_length = math.sqrt((x_N[i+1]-x_N[i])**2 + (r_N[i+1]-r_N[i])**2)
            m_prime_N_final[i+1] = m_prime_N_final[i] + segment_length
        # Adjust start if t_current_interp starts negative (only for first stage's full range)
        if t_current_interp[0] < 0.0:
            # Find the index where t_current_interp crosses 0, and shift all values so 0 starts at 0 arc length
             # Ensure the index is valid; if 0.0 is not directly in t_current_interp, find the closest
            start_idx = np.searchsorted(t_current_interp, 0.0)
            initial_m_val = m_prime_N_final[start_idx]
            m_prime_N_final = [val - initial_m_val for val in m_prime_N_final]
        all_m_prime_N_stages.append(m_prime_N_final)

        m_prime_G_final = [0.0] * len(t_current_interp)
        for i in range(len(t_current_interp)-1):
            segment_length = math.sqrt((x_G[i+1]-x_G[i])**2+(r_G[i+1]-r_G[i])**2)
            m_prime_G_final[i+1] = m_prime_G_final[i] + segment_length
        # Adjust start if t_current_interp starts negative (only for first stage's full range)
        if t_current_interp[0] < 0.0:
            start_idx = np.searchsorted(t_current_interp, 0.0)
            initial_m_val = m_prime_G_final[start_idx]
            m_prime_G_final = [val - initial_m_val for val in m_prime_G_final]
        all_m_prime_G_stages.append(m_prime_G_final)
        
        # Calculate intermediate lines for the current stage based on h_H
        x_values_stage = []
        r_values_stage = []
        m_prime_values_stage = []
        for _ in range(len(h_H)):
            x_values_stage.append([])
            r_values_stage.append([])
            m_prime_values_stage.append([])

        for k, element in enumerate(h_H):
            for i in range(len(t_current_interp)): # Use t_current_interp
                x_values_stage[k].append(x_N[i]+element*(x_G[i]-x_N[i]))
                r_values_stage[k].append(r_N[i]+element*(r_G[i]-r_N[i]))
                m_prime_values_stage[k].append(m_prime_N_final[i]+element*(m_prime_G_final[i]-m_prime_N_final[i]))
        
        
        all_x_values_stages.append(x_values_stage)
        all_r_values_stages.append(r_values_stage)
        all_m_prime_values_stages.append(m_prime_values_stage)

        # Update axial offset for the next stage
        # The new offset is the last x-coordinate of the *interpolated* path for the current stage.
        # This ensures smooth connection of the lines.
        current_axial_offset = x_N[-1] # Using x_N[-1] or x_G[-1] as they are the same
    
    # Mirroring of Shroud and Hub radii (R_G, R_N) - for plotting below axis
    # These will now be lists of lists
    all_R_G_stages = []
    all_R_N_stages = []
    for stage_idx in range(i_st):
        R_G_stage = []
        R_N_stage = []
        # Use the actual interpolated points for mirroring, which are now filtered by t_current_interp
        for i in range(len(all_r_G_stages[stage_idx])):
            R_G_stage.append(-all_r_G_stages[stage_idx][i])
            R_N_stage.append(-all_r_N_stages[stage_idx][i])
        all_R_G_stages.append(R_G_stage)
        all_R_N_stages.append(R_N_stage)
    
    
    plt.figure(figsize=(12, 6)) # Adjust figure size for multi-stage view
    
    # Redefine how combined_x0, combined_r0_N, combined_r0_G are generated for scatter plot
    # This ensures that only the relevant control points for the *entire* channel are plotted,
    # avoiding redundant or misleading points at stage boundaries.
    combined_x0_scatter = []
    combined_r0_N_scatter = []
    combined_r0_G_scatter = []
    combined_channelHeight_at_x0_scatter = [] # New list for channel height at scatter points

    # Use a set to keep track of already added (x, rN, rG) tuples to avoid duplicates
    added_control_points = set()

    for stage_idx in range(i_st):
        x0_s = all_x0_stages[stage_idx]
        r0_N_s = all_r0_N_stages[stage_idx]
        r0_G_s = all_r0_G_stages[stage_idx]
        channelHeight_stage_interp = all_channelHeight_stages[stage_idx] # Interpolated values for this stage
        x_N_interp = all_x_N_stages[stage_idx] # Interpolated x values for this stage

        # Logic for selecting which control points to plot as scatter points for the combined channel
        current_stage_control_point_indices = []
        if i_st == 1:
            # If only one stage, plot all control points from 0 to 8
            current_stage_control_point_indices = range(len(x0_s))
        elif stage_idx == 0:
            # For the first stage (of multiple stages), plot from 0 to 7. Point 8 is an internal connection.
            current_stage_control_point_indices = range(8) # 0 to 7
        elif stage_idx == i_st - 1:
            # For the last stage (of multiple stages), plot from 1 to 8. Point 0 is an internal connection.
            current_stage_control_point_indices = range(1, 9) # 1 to 8
        else:
            # For intermediate stages, plot from 1 to 7. Points 0 and 8 are internal connections.
            current_stage_control_point_indices = range(1, 8) # 1 to 7

        for idx in current_stage_control_point_indices:
            x_val = x0_s[idx]
            r_N_val = r0_N_s[idx]
            r_G_val = r0_G_s[idx]
            
            point_tuple = (x_val, r_N_val, r_G_val)
            if point_tuple not in added_control_points:
                combined_x0_scatter.append(x_val)
                combined_r0_N_scatter.append(r_N_val)
                combined_r0_G_scatter.append(r_G_val)
                added_control_points.add(point_tuple)

                # Find and append corresponding channel height value
                # Find the closest interpolated x-value for this control point's x-coordinate
                closest_interp_idx = np.argmin(np.abs(np.array(x_N_interp) - x_val))
                if abs(x_N_interp[closest_interp_idx] - x_val) < 1e-6: # Check if it's truly close
                    combined_channelHeight_at_x0_scatter.append(channelHeight_stage_interp[closest_interp_idx])
                else:
                    # Fallback if an exact match isn't found (shouldn't happen for control points)
                    combined_channelHeight_at_x0_scatter.append(r_G_val - r_N_val)


    # Sort the combined lists by x-coordinate to ensure correct plotting order for labels
    # It's important to sort all lists consistently based on combined_x0_scatter
    sorted_indices = np.argsort(combined_x0_scatter)
    combined_x0_scatter = np.array(combined_x0_scatter)[sorted_indices]
    combined_r0_N_scatter = np.array(combined_r0_N_scatter)[sorted_indices]
    combined_r0_G_scatter = np.array(combined_r0_G_scatter)[sorted_indices]
    combined_channelHeight_at_x0_scatter = np.array(combined_channelHeight_at_x0_scatter)[sorted_indices]

    # Now use these combined_scatter lists for plotting and labeling
    plt.scatter(combined_x0_scatter, combined_r0_N_scatter, label=f'Hub Control Points (Overall)', color='gray', marker='o', s=20)
    plt.scatter(combined_x0_scatter, combined_r0_G_scatter, label=f'Shroud Control Points (Overall)', color='gray', marker='x', s=20)

    # The combined_channelHeight_x and combined_channelHeight_val should aggregate all interpolated channel heights
    combined_channelHeight_x = []
    combined_channelHeight_val = []
    for stage_idx in range(i_st):
        combined_channelHeight_x.extend(all_x_N_stages[stage_idx])
        combined_channelHeight_val.extend(all_channelHeight_stages[stage_idx])

    # Sort combined channel height for plotting
    combined_channelHeight_sort_indices = np.argsort(combined_channelHeight_x)
    combined_channelHeight_x = np.array(combined_channelHeight_x)[combined_channelHeight_sort_indices]
    combined_channelHeight_val = np.array(combined_channelHeight_val)[combined_channelHeight_sort_indices]

    plt.plot(combined_channelHeight_x, combined_channelHeight_val, label='Channel Height (Overall)', color='purple', linestyle='-.', marker='s', markersize=1)

    # Add text labels for radii at control points for all stages combined
    plot_label = 0 # Add labels (radii) to the Plot
    if plot_label:
        for i in range(len(combined_x0_scatter)): 
            # Label for Hub radius
            plt.text(combined_x0_scatter[i], combined_r0_N_scatter[i], 
                        f"({combined_r0_N_scatter[i]:.3f})", fontsize=8, ha='right', va='top', color='blue') 

            # Label for Shroud radius
            plt.text(combined_x0_scatter[i], combined_r0_G_scatter[i], 
                        f"({combined_r0_G_scatter[i]:.3f})", fontsize=8, ha='right', va='bottom', color='red') 

            # Label for Channel Height
            plt.text(combined_x0_scatter[i], combined_channelHeight_at_x0_scatter[i], 
                        f"({combined_channelHeight_at_x0_scatter[i]:.3f})", fontsize=8, ha='left', va='bottom', color='green') 

    
    
    
    for stage_idx in range(i_st):

        x_N = all_x_N_stages[stage_idx]
        r_N = all_r_N_stages[stage_idx]
        x_G = all_x_G_stages[stage_idx]
        r_G = all_r_G_stages[stage_idx]
        meanline_stage = all_meanline_stages[stage_idx]
        channelHeight_stage = all_channelHeight_stages[stage_idx]
        R_N_stage = all_R_N_stages[stage_idx]
        R_G_stage = all_R_G_stages[stage_idx]


        #plt.scatter(x0, r0_N, label=f'Hub Control Points Stage {stage_idx+1}')
        #plt.scatter(x0, r0_G, label=f'Shroud Control Points Stage {stage_idx+1}')
        
        plt.plot(x_N, r_N, label = f'Hub Stage {stage_idx+1}', color=f'C{stage_idx}')
        plt.plot(x_G, r_G, label = f'Shroud Stage {stage_idx+1}', color=f'C{stage_idx}')
        plt.plot(x_G, meanline_stage, linestyle='--', label = f'Meanline Stage {stage_idx+1}', color=f'C{stage_idx}')
        
        # Optionally plot mirrored parts
        if plot_mirrored==1:
            plt.plot(x_N, R_N_stage, color=f'C{stage_idx}', linestyle=':')
            plt.plot(x_G, R_G_stage, color=f'C{stage_idx}', linestyle=':')

        # Plot channel height at control points (using x0 for x-coords)
        #plt.plot(x0, channelHeight_stage, label = f'Channel Height Stage {stage_idx+1}', color=f'C{stage_idx}', marker='x', linestyle='-.')
        # Text for channel height on the plot for each stage
        #for i in range(len(x0)):
        #    plt.text(round(x0[i],1), round(channelHeight_stage[i],1), f"({round(channelHeight_stage[i],1)})", fontsize=8, ha='right', va='bottom') 
        #    plt.text(round(x0[i],1), round(r0_G[i],1), f"({round(r0_G[i],1)})", fontsize=8, ha='right', va='bottom')
        
    plt.axis('equal')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left') # Move legend outside to prevent overlap
    plt.ylabel('Radii [mm]')
    plt.xlabel('Axial Length [mm]')
    plt.title('Channel Geometry for All Stages (Smoothed Transitions)') # Added "Smoothed Transitions" to title
    plt.grid(True)
    plt.tight_layout() # Adjust layout to prevent labels from being cut off
    
    debug_log.debug("Attempting to show plot window...", context="plot_channel")
    plt.show(block=True) # Ensure the plot window blocks execution until closed
    debug_log.debug("Plot window closed or script continued.", context="plot_channel")
# The return values should now be lists of lists, one for each stage