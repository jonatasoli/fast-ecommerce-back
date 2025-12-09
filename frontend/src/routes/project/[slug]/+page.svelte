<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api';
	import ContributionForm from '$lib/components/ContributionForm.svelte';

	let project = null;
	let tiers = [];
	let goals = [];
	let monthlyGoals = [];
	let summary = null;
	let loading = true;
	let error = null;
	let selectedTier = null;
	let showContributionForm = false;

	$: slug = $page.params.slug;

	onMount(async () => {
		try {
			project = await api.getProjectBySlug(slug);
			tiers = await api.listTiers(project.project_id);
			goals = await api.listGoals(project.project_id);
			monthlyGoals = await api.listMonthlyGoals(project.project_id);
			summary = await api.getProjectSummary(project.project_id);
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	});

	function selectTier(tier) {
		selectedTier = tier;
		showContributionForm = true;
	}

	function handleContributionSuccess() {
		showContributionForm = false;
		// Reload data
		location.reload();
	}
</script>

<svelte:head>
	<title>{project?.title || 'Projeto'}</title>
</svelte:head>

{#if loading}
	<p>Carregando projeto...</p>
{:else if error}
	<p class="error">Erro: {error}</p>
{:else if project}
	<div class="project-page">
		<!-- Hero Section -->
		<div class="hero">
			{#if project.main_image}
				<img src={project.main_image} alt={project.title} />
			{/if}
			<div class="hero-content">
				<h1>{project.title}</h1>
				<p class="short-description">{project.short_description}</p>
			</div>
		</div>

		<div class="container">
			<div class="main-content">
				<!-- Story Section -->
				{#if project.story}
					<section class="story">
						<h2>A História</h2>
						<div class="story-content">
							{#if typeof project.story === 'string'}
								{@html project.story}
							{:else}
								{JSON.stringify(project.story)}
							{/if}
						</div>
					</section>
				{/if}

				<!-- Risks Section -->
				{#if project.risks_and_challenges}
					<section class="risks">
						<h2>Riscos e Desafios</h2>
						<div class="risks-content">
							{#if typeof project.risks_and_challenges === 'string'}
								{@html project.risks_and_challenges}
							{:else}
								{JSON.stringify(project.risks_and_challenges)}
							{/if}
						</div>
					</section>
				{/if}
			</div>

			<div class="sidebar">
				<!-- Progress Section -->
				<div class="progress-card">
					<div class="progress-info">
						<div class="amount">
							<span class="current">R$ {project.current_amount.toFixed(2)}</span>
							<span class="goal">de R$ {project.goal_amount.toFixed(2)}</span>
						</div>
						<div class="progress-bar">
							<div
								class="progress-fill"
								style="width: {Math.min((project.current_amount / project.goal_amount) * 100, 100)}%"
							></div>
						</div>
						<div class="stats">
							<span>{project.backers_count} apoiadores</span>
						</div>
					</div>
				</div>

				<!-- Tiers Section -->
				<div class="tiers-section">
					<h3>Escolha seu nível de apoio</h3>
					<div class="tiers-list">
						{#each tiers as tier}
							<div class="tier-card" class:selected={selectedTier?.tier_id === tier.tier_id}>
								<div class="tier-header">
									<h4>{tier.name}</h4>
									<div class="tier-amount">R$ {tier.amount.toFixed(2)}</div>
								</div>
								{#if tier.description}
									<p class="tier-description">{tier.description}</p>
								{/if}
								<div class="tier-meta">
									{#if tier.is_recurring}
										<span class="recurring">Recorrente ({tier.recurring_interval})</span>
									{:else}
										<span class="one-time">Pagamento único</span>
									{/if}
									{#if tier.max_backers}
										<span class="backers">
											{tier.current_backers} / {tier.max_backers} apoiadores
										</span>
									{/if}
								</div>
								<button class="select-tier" on:click={() => selectTier(tier)} disabled={tier.max_backers && tier.current_backers >= tier.max_backers}>
									Selecionar
								</button>
							</div>
						{/each}
					</div>
				</div>

				<!-- Goals Section -->
				{#if goals.length > 0}
					<div class="goals-section">
						<h3>Metas</h3>
						<div class="goals-list">
							{#each goals as goal}
								<div class="goal-item">
									<h4>{goal.title}</h4>
									{#if goal.description}
										<p>{goal.description}</p>
									{/if}
									<div class="goal-progress">
										<div class="goal-amount">
											R$ {goal.current_amount.toFixed(2)} / R$ {goal.target_amount.toFixed(2)}
										</div>
										<div class="progress-bar small">
											<div
												class="progress-fill"
												style="width: {Math.min((goal.current_amount / goal.target_amount) * 100, 100)}%"
											></div>
										</div>
										{#if goal.achieved}
											<span class="achieved">✓ Meta alcançada!</span>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Monthly Goals Section -->
				{#if monthlyGoals.length > 0}
					<div class="monthly-goals-section">
						<h3>Metas Mensais</h3>
						<div class="monthly-goals-list">
							{#each monthlyGoals as monthlyGoal}
								<div class="monthly-goal-item">
									<h4>
										{['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][monthlyGoal.month - 1]} {monthlyGoal.year}
									</h4>
									<div class="monthly-goal-progress">
										<div class="monthly-goal-amount">
											R$ {monthlyGoal.current_amount.toFixed(2)} / R$ {monthlyGoal.target_amount.toFixed(2)}
										</div>
										<div class="progress-bar small">
											<div
												class="progress-fill"
												style="width: {Math.min((monthlyGoal.current_amount / monthlyGoal.target_amount) * 100, 100)}%"
											></div>
										</div>
										<div class="monthly-total">
											Total pago no mês: R$ {monthlyGoal.total_paid_in_month.toFixed(2)}
										</div>
										{#if monthlyGoal.achieved}
											<span class="achieved">✓ Meta alcançada!</span>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>

	<!-- Contribution Form Modal -->
	{#if showContributionForm && selectedTier}
		<div class="modal-overlay" on:click={() => showContributionForm = false}>
			<div class="modal-content" on:click|stopPropagation>
				<ContributionForm
					{project}
					{selectedTier}
					on:success={handleContributionSuccess}
					on:cancel={() => showContributionForm = false}
				/>
			</div>
		</div>
	{/if}
{/if}

<style>
	.project-page {
		min-height: 100vh;
	}

	.hero {
		position: relative;
		height: 400px;
		overflow: hidden;
	}

	.hero img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.hero-content {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
		color: white;
		padding: 2rem;
	}

	.hero-content h1 {
		margin: 0 0 0.5rem 0;
		font-size: 2rem;
	}

	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
		display: grid;
		grid-template-columns: 2fr 1fr;
		gap: 2rem;
	}

	.main-content {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	.sidebar {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	.progress-card {
		background: #f5f5f5;
		padding: 1.5rem;
		border-radius: 8px;
	}

	.amount {
		display: flex;
		flex-direction: column;
		margin-bottom: 1rem;
	}

	.amount .current {
		font-size: 2rem;
		font-weight: bold;
		color: #00c853;
	}

	.amount .goal {
		font-size: 1rem;
		color: #666;
	}

	.progress-bar {
		height: 12px;
		background: #e0e0e0;
		border-radius: 6px;
		overflow: hidden;
		margin: 1rem 0;
	}

	.progress-bar.small {
		height: 6px;
	}

	.progress-fill {
		height: 100%;
		background: #00c853;
		transition: width 0.3s;
	}

	.tiers-section h3,
	.goals-section h3,
	.monthly-goals-section h3 {
		margin: 0 0 1rem 0;
	}

	.tiers-list,
	.goals-list,
	.monthly-goals-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.tier-card {
		border: 2px solid #e0e0e0;
		border-radius: 8px;
		padding: 1rem;
		transition: border-color 0.2s;
	}

	.tier-card.selected {
		border-color: #00c853;
	}

	.tier-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.tier-amount {
		font-size: 1.5rem;
		font-weight: bold;
		color: #00c853;
	}

	.tier-description {
		margin: 0.5rem 0;
		color: #666;
		font-size: 0.9rem;
	}

	.tier-meta {
		display: flex;
		gap: 1rem;
		font-size: 0.85rem;
		color: #666;
		margin: 0.5rem 0;
	}

	.select-tier {
		width: 100%;
		padding: 0.75rem;
		background: #00c853;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-weight: bold;
		margin-top: 0.5rem;
	}

	.select-tier:hover:not(:disabled) {
		background: #00a043;
	}

	.select-tier:disabled {
		background: #ccc;
		cursor: not-allowed;
	}

	.goal-item,
	.monthly-goal-item {
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		padding: 1rem;
	}

	.goal-progress,
	.monthly-goal-progress {
		margin-top: 0.5rem;
	}

	.goal-amount,
	.monthly-goal-amount {
		font-size: 0.9rem;
		color: #666;
		margin-bottom: 0.5rem;
	}

	.monthly-total {
		font-size: 0.85rem;
		color: #999;
		margin-top: 0.5rem;
	}

	.achieved {
		color: #00c853;
		font-weight: bold;
		font-size: 0.9rem;
		display: block;
		margin-top: 0.5rem;
	}

	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.modal-content {
		background: white;
		border-radius: 8px;
		padding: 2rem;
		max-width: 500px;
		width: 90%;
		max-height: 90vh;
		overflow-y: auto;
	}

	.error {
		color: #d32f2f;
	}

	@media (max-width: 768px) {
		.container {
			grid-template-columns: 1fr;
		}
	}
</style>
